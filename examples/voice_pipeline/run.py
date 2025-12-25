#!/usr/bin/env python3
"""Simple voice chat pipeline with voiceobs instrumentation.

This example demonstrates how to instrument a voice pipeline with voiceobs,
including stage-level spans for ASR, LLM, and TTS operations.

Requirements:
    pip install voiceobs python-dotenv google-genai deepgram-sdk cartesia sounddevice numpy

Environment variables (create .env file):
    DEEPGRAM_API_KEY=your_deepgram_key
    GOOGLE_API_KEY=your_google_key
    CARTESIA_API_KEY=your_cartesia_key

Usage:
    python run.py
"""

import asyncio
import io
import os
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
SAMPLE_RATE = 16000  # Deepgram and Cartesia compatibility
CHANNELS = 1


def record_audio_vad(
    silence_threshold: int = 200,
    silence_duration: float = 1.0,
    max_duration: int = 30,
) -> bytes | None:
    """Record audio with Voice Activity Detection.

    Stops recording after silence_duration seconds of silence.

    Args:
        silence_threshold: RMS amplitude below which is considered silence
        silence_duration: Seconds of silence to wait before stopping
        max_duration: Maximum recording duration in seconds

    Returns:
        WAV audio bytes, or None if no speech detected
    """
    print("Listening... (speak now, recording will stop when you pause)")

    audio_chunks = []
    silent_chunks = 0
    chunk_duration = 0.1  # 100ms chunks
    chunk_samples = int(SAMPLE_RATE * chunk_duration)
    chunks_for_silence = int(silence_duration / chunk_duration)
    max_chunks = int(max_duration / chunk_duration)

    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
    stream.start()

    has_speech = False
    chunk_count = 0

    try:
        while chunk_count < max_chunks:
            chunk, _ = stream.read(chunk_samples)
            audio_chunks.append(chunk.copy())
            chunk_count += 1

            # Calculate RMS amplitude
            rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))

            if rms > silence_threshold:
                has_speech = True
                silent_chunks = 0
            elif has_speech:
                silent_chunks += 1
                if silent_chunks >= chunks_for_silence:
                    break
    finally:
        stream.stop()
        stream.close()

    if not has_speech:
        print("No speech detected.")
        return None

    print("Recording finished.")

    # Concatenate all chunks
    recording = np.concatenate(audio_chunks)

    # Wrap raw PCM in WAV container for Deepgram
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(2)  # 16-bit = 2 bytes
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(recording.tobytes())

    return wav_buffer.getvalue()


def play_audio(audio_data: bytes, rate: int = 44100) -> None:
    """Play audio data."""
    audio_np = np.frombuffer(audio_data, dtype=np.float32)
    sd.play(audio_np, samplerate=rate)
    sd.wait()


def transcribe_audio(audio_bytes: bytes) -> str | None:
    """Transcribe audio bytes using Deepgram.

    Args:
        audio_bytes: WAV audio data

    Returns:
        Transcribed text, or None if no speech detected
    """
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


def generate_response(user_text: str) -> str:
    """Generate AI response using Gemini.

    Args:
        user_text: User's transcribed text

    Returns:
        AI-generated response text
    """
    print("Generating response with Gemini...")

    with voice_stage(
        "llm",
        provider="google",
        model="gemini-2.0-flash",
        input_size=len(user_text),
    ) as llm:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_text,
        )
        result = response.text
        llm.set_output(len(result))
        return result


def synthesize_speech(
    text: str,
    voice_id: str = "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
) -> bytes:
    """Convert text to speech using Cartesia.

    Args:
        text: Text to synthesize
        voice_id: Cartesia voice ID

    Returns:
        Raw PCM audio bytes
    """
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


async def pipeline() -> None:
    """Main voice chat pipeline loop with observability."""
    print("=" * 50)
    print("Simple Voice Chat Pipeline (with voiceobs)")
    print("=" * 50)
    print("Press Ctrl+C to exit.\n")

    while True:
        try:
            input("Press Enter to start listening...")

            # Each conversation is wrapped in voice_conversation
            with voice_conversation() as conv:
                print(f"\n[Conversation: {conv.conversation_id}]")

                # User turn: capture and transcribe audio
                with voice_turn("user"):
                    audio_bytes = record_audio_vad()
                    if audio_bytes is None:
                        continue

                    # Mark when user stopped speaking (recording finished)
                    mark_speech_end()

                    transcript = transcribe_audio(audio_bytes)
                    if not transcript:
                        print("No speech detected.")
                        continue
                    print(f"\nUser: {transcript}")

                # Get user turn duration from timeline
                user_turn = conv.timeline.get_last_turn_by_actor("user")
                if user_turn and user_turn.duration_ms:
                    print(f"[User turn duration: {user_turn.duration_ms:.0f}ms]")

                # Agent turn: generate and speak response
                with voice_turn("agent"):
                    ai_text = generate_response(transcript)
                    print(f"\nAI: {ai_text}")

                    # Synthesize speech
                    audio = synthesize_speech(ai_text)

                    # Mark when agent starts speaking (just before playback)
                    mark_speech_start()

                    # Print response latency (user speech end -> agent speech start)
                    latency_ms = conv.timeline.compute_response_latency_ms()
                    if latency_ms is not None:
                        print(f"[Response latency: {latency_ms:.0f}ms]")

                    play_audio(audio, rate=44100)

                # Get agent turn duration from timeline
                agent_turn = conv.timeline.get_last_turn_by_actor("agent")
                if agent_turn and agent_turn.duration_ms:
                    print(f"[Agent turn duration: {agent_turn.duration_ms:.0f}ms]")

                print("\n[Conversation ended]")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(pipeline())
