#!/usr/bin/env python3
"""Voice pipeline demonstrating overlap/interruption detection.

This example shows how voiceobs tracks overlap between user and agent speech.
It includes a "barge-in" mode where the agent can intentionally interrupt
long user messages to demonstrate overlap detection.

Setup:
    cd examples/overlap_detection
    cp .env.example .env  # Add your API keys
    uv sync

Environment variables (.env file):
    DEEPGRAM_API_KEY=your_deepgram_key
    GOOGLE_API_KEY=your_google_key
    CARTESIA_API_KEY=your_cartesia_key

Usage:
    uv run python run.py              # Normal mode
    uv run python run.py --barge-in   # Barge-in mode (agent interrupts after 2s)
"""

import argparse
import asyncio
import io
import os
import time
import wave

import numpy as np
import sounddevice as sd
from cartesia import Cartesia
from deepgram import DeepgramClient
from dotenv import load_dotenv
from google import genai

from voiceobs import (
    ensure_tracing_initialized,
    mark_speech_end,
    mark_speech_start,
    voice_conversation,
    voice_stage,
    voice_turn,
)

# Load environment variables
load_dotenv()

# Initialize observability tracing
ensure_tracing_initialized()

# Configuration
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")

# Check for API keys
if not all([DEEPGRAM_API_KEY, GOOGLE_API_KEY, CARTESIA_API_KEY]):
    print("Error: Missing API keys. Please check your .env file.")
    print("Required: DEEPGRAM_API_KEY, GOOGLE_API_KEY, CARTESIA_API_KEY")
    exit(1)

# Initialize Clients
deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
cartesia = Cartesia(api_key=CARTESIA_API_KEY)

# Audio Configuration
SAMPLE_RATE = 16000
CHANNELS = 1


class BargeInRecorder:
    """Audio recorder that supports barge-in (early stopping)."""

    def __init__(
        self,
        silence_threshold: int = 200,
        silence_duration: float = 1.0,
        max_duration: int = 30,
        barge_in_after_ms: int | None = None,
    ):
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.max_duration = max_duration
        self.barge_in_after_ms = barge_in_after_ms

        self.audio_chunks: list[np.ndarray] = []
        self.is_recording = False
        self.barge_in_triggered = False
        self.barge_in_time_ns: int | None = None  # Timestamp when barge-in triggered
        self.speech_end_time: float | None = None
        self.has_speech = False

    def record(self) -> bytes | None:
        """Record audio with optional barge-in support.

        Returns:
            WAV audio bytes, or None if no speech detected
        """
        if self.barge_in_after_ms:
            print(f"Listening... (barge-in enabled after {self.barge_in_after_ms}ms)")
        else:
            print("Listening... (speak now, recording will stop when you pause)")

        self.audio_chunks = []
        silent_chunks = 0
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(SAMPLE_RATE * chunk_duration)
        chunks_for_silence = int(self.silence_duration / chunk_duration)
        max_chunks = int(self.max_duration / chunk_duration)

        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
        stream.start()

        self.has_speech = False
        self.is_recording = True
        self.barge_in_triggered = False
        chunk_count = 0
        speech_start_time = None

        try:
            while chunk_count < max_chunks and self.is_recording:
                chunk, _ = stream.read(chunk_samples)
                self.audio_chunks.append(chunk.copy())
                chunk_count += 1

                # Calculate RMS amplitude
                rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

                if rms > self.silence_threshold:
                    if not self.has_speech:
                        speech_start_time = time.time()
                        print("🎤 Speech detected, recording...")
                    self.has_speech = True
                    silent_chunks = 0

                    # Check for barge-in
                    if self.barge_in_after_ms and speech_start_time:
                        elapsed_ms = (time.time() - speech_start_time) * 1000
                        # Show countdown
                        if elapsed_ms >= 1000 and elapsed_ms < 1100:
                            print("   1 second...")
                        if elapsed_ms >= self.barge_in_after_ms:
                            print("\n⚡ BARGE-IN: Agent interrupting!")
                            self.barge_in_triggered = True
                            # Capture the barge-in timestamp - this is when agent
                            # logically starts speaking (user is still talking!)
                            import time as time_module

                            self.barge_in_time_ns = time_module.time_ns()
                            break
                elif self.has_speech:
                    silent_chunks += 1
                    if silent_chunks >= chunks_for_silence:
                        break
        finally:
            self.is_recording = False
            stream.stop()
            stream.close()

        if not self.has_speech:
            print("No speech detected.")
            return None

        if not self.barge_in_triggered:
            print("Recording finished.")

        # Record when speech ended (for overlap calculation)
        self.speech_end_time = time.time()

        # Concatenate all chunks
        recording = np.concatenate(self.audio_chunks)

        # Wrap raw PCM in WAV container
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(recording.tobytes())

        return wav_buffer.getvalue()


def play_audio(audio_data: bytes, rate: int = 44100) -> None:
    """Play audio data."""
    audio_np = np.frombuffer(audio_data, dtype=np.float32)
    sd.play(audio_np, samplerate=rate)
    sd.wait()


def transcribe_audio(audio_bytes: bytes) -> str | None:
    """Transcribe audio bytes using Deepgram."""
    print("Transcribing with Deepgram...")

    with voice_stage(
        "asr",
        provider="deepgram",
        model="nova-2",
        input_size=len(audio_bytes),
    ) as asr:
        response = deepgram.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model="nova-2",
            language="en",
            smart_format=True,
        )
        transcript = response.results.channels[0].alternatives[0].transcript
        if transcript:
            asr.set_output(len(transcript))
        return transcript if transcript else None


def generate_response(user_text: str, is_barge_in: bool = False) -> str:
    """Generate AI response using Gemini."""
    print("Generating response with Gemini...")

    # If barge-in, add context to the prompt
    if is_barge_in:
        prompt = f"""The user was saying: "{user_text}"

You interrupted them because you understood their intent early.
Respond briefly and acknowledge you got the gist of what they were saying."""
    else:
        prompt = user_text

    with voice_stage(
        "llm",
        provider="google",
        model="gemini-2.0-flash",
        input_size=len(prompt),
    ) as llm:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        result = response.text
        llm.set_output(len(result))
        return result


def synthesize_speech(
    text: str,
    voice_id: str = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
) -> bytes:
    """Convert text to speech using Cartesia."""
    print("Synthesizing speech with Cartesia...")

    with voice_stage(
        "tts",
        provider="cartesia",
        model="sonic-3",
        input_size=len(text),
    ) as tts:
        audio_chunks = cartesia.tts.bytes(
            model_id="sonic-3",
            transcript=text,
            voice={"id": voice_id},
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 44100,
            },
            language="en",
        )
        audio_data = b"".join(audio_chunks)
        tts.set_output(len(audio_data))
        return audio_data


async def pipeline(barge_in_mode: bool = False) -> None:
    """Main voice chat pipeline with overlap detection.

    Args:
        barge_in_mode: If True, agent will interrupt after 2 seconds of user speech
    """
    print("=" * 60)
    print("Overlap Detection Voice Pipeline")
    print("=" * 60)
    if barge_in_mode:
        print("MODE: Barge-in enabled - Agent will interrupt after 2s of speech")
        print("TIP: Speak for longer than 2 seconds to see overlap detection!")
    else:
        print("MODE: Normal - Agent waits for user to finish")
        print("TIP: Run with --barge-in to see overlap detection in action")
    print("Press Ctrl+C to exit.\n")

    while True:
        try:
            input("Press Enter to start listening...")

            with voice_conversation() as conv:
                print(f"\n[Conversation: {conv.conversation_id[:8]}...]")

                # Create recorder with optional barge-in
                recorder = BargeInRecorder(barge_in_after_ms=2000 if barge_in_mode else None)

                # User turn
                with voice_turn("user"):
                    audio_bytes = recorder.record()
                    if audio_bytes is None:
                        continue

                    # Mark speech end - this is when user stopped speaking
                    # In barge-in mode, user might still be speaking when we proceed
                    mark_speech_end()

                    transcript = transcribe_audio(audio_bytes)
                    if not transcript:
                        print("No speech detected.")
                        continue
                    print(f"\nUser: {transcript}")

                # Print user turn metrics
                user_turn = conv.timeline.get_last_turn_by_actor("user")
                if user_turn and user_turn.duration_ms:
                    print(f"[User turn: {user_turn.duration_ms:.0f}ms]")

                # Agent turn
                with voice_turn("agent"):
                    ai_text = generate_response(transcript, is_barge_in=recorder.barge_in_triggered)
                    print(f"\nAI: {ai_text}")

                    # Synthesize speech
                    audio = synthesize_speech(ai_text)

                    # Mark when agent starts speaking
                    # In barge-in mode, use the barge-in timestamp to show
                    # that agent logically started speaking while user was still talking
                    if recorder.barge_in_triggered and recorder.barge_in_time_ns:
                        mark_speech_start(timestamp_ns=recorder.barge_in_time_ns)
                    else:
                        mark_speech_start()

                    # Print response latency
                    latency_ms = conv.timeline.compute_response_latency_ms()
                    if latency_ms is not None:
                        print(f"[Response latency: {latency_ms:.0f}ms]")

                    play_audio(audio, rate=44100)

                # Print agent turn metrics
                agent_turn = conv.timeline.get_last_turn_by_actor("agent")
                if agent_turn and agent_turn.duration_ms:
                    print(f"[Agent turn: {agent_turn.duration_ms:.0f}ms]")

                # Print overlap detection results
                overlap_ms = conv.timeline.compute_overlap_ms()
                if overlap_ms is not None:
                    if conv.timeline.is_interruption():
                        print(f"\n⚠️  OVERLAP DETECTED: Agent interrupted by {overlap_ms:.0f}ms")
                        print("   (Agent started speaking before user finished)")
                    else:
                        print(f"\n✓ Normal turn-taking: {-overlap_ms:.0f}ms gap between speakers")

                print("\n[Conversation ended]")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Overlap Detection Voice Pipeline")
    parser.add_argument(
        "--barge-in",
        action="store_true",
        help="Enable barge-in mode (agent interrupts after 2s)",
    )
    args = parser.parse_args()

    asyncio.run(pipeline(barge_in_mode=args.barge_in))
