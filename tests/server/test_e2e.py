"""End-to-end tests for the voiceobs server.

These tests verify the complete workflow: ingest → analyze → verify failures.
"""


class TestEndToEndWorkflow:
    """End-to-end tests for complete server workflows."""

    def test_ingest_analyze_failures_workflow(self, client):
        """Test complete workflow: ingest spans → analyze → check failures."""
        # Step 1: Ingest a realistic conversation with multiple turns
        conversation_spans = {
            "spans": [
                # User turn 1
                {
                    "name": "voice.turn",
                    "duration_ms": 2000.0,
                    "attributes": {
                        "voice.actor": "user",
                        "voice.conversation.id": "e2e-conv-1",
                        "voice.turn.id": "turn-1",
                        "voice.turn.index": 0,
                    },
                },
                # ASR stage
                {
                    "name": "voice.asr",
                    "duration_ms": 150.0,
                    "attributes": {
                        "voice.stage.type": "asr",
                        "voice.conversation.id": "e2e-conv-1",
                    },
                },
                # Agent turn 1 (with slow LLM)
                {
                    "name": "voice.turn",
                    "duration_ms": 3500.0,
                    "attributes": {
                        "voice.actor": "agent",
                        "voice.conversation.id": "e2e-conv-1",
                        "voice.turn.id": "turn-2",
                        "voice.turn.index": 1,
                    },
                },
                # Slow LLM stage (should trigger failure)
                {
                    "name": "voice.llm",
                    "duration_ms": 5000.0,  # 5 seconds - should trigger slow_response
                    "attributes": {
                        "voice.stage.type": "llm",
                        "voice.conversation.id": "e2e-conv-1",
                    },
                },
                # TTS stage
                {
                    "name": "voice.tts",
                    "duration_ms": 200.0,
                    "attributes": {
                        "voice.stage.type": "tts",
                        "voice.conversation.id": "e2e-conv-1",
                    },
                },
                # User turn 2
                {
                    "name": "voice.turn",
                    "duration_ms": 1500.0,
                    "attributes": {
                        "voice.actor": "user",
                        "voice.conversation.id": "e2e-conv-1",
                        "voice.turn.id": "turn-3",
                        "voice.turn.index": 2,
                    },
                },
                # Agent turn 2
                {
                    "name": "voice.turn",
                    "duration_ms": 2000.0,
                    "attributes": {
                        "voice.actor": "agent",
                        "voice.conversation.id": "e2e-conv-1",
                        "voice.turn.id": "turn-4",
                        "voice.turn.index": 3,
                    },
                },
            ]
        }

        # Ingest spans
        ingest_response = client.post("/ingest", json=conversation_spans)
        assert ingest_response.status_code == 201
        assert ingest_response.json()["accepted"] == 7

        # Step 2: Verify spans were stored
        spans_response = client.get("/spans")
        assert spans_response.status_code == 200
        assert spans_response.json()["count"] == 7

        # Step 3: Analyze all spans
        analyze_response = client.get("/analyze")
        assert analyze_response.status_code == 200
        analysis = analyze_response.json()

        assert analysis["summary"]["total_spans"] == 7
        assert analysis["summary"]["total_conversations"] == 1
        assert analysis["summary"]["total_turns"] == 4
        assert analysis["stages"]["asr"]["count"] == 1
        assert analysis["stages"]["llm"]["count"] == 1
        assert analysis["stages"]["tts"]["count"] == 1

        # Step 4: Analyze specific conversation
        conv_response = client.get("/analyze/e2e-conv-1")
        assert conv_response.status_code == 200
        conv_analysis = conv_response.json()
        assert conv_analysis["summary"]["total_turns"] == 4

        # Step 5: Get conversation details
        conv_detail = client.get("/conversations/e2e-conv-1")
        assert conv_detail.status_code == 200
        detail = conv_detail.json()
        assert detail["id"] == "e2e-conv-1"
        assert len(detail["turns"]) == 4
        assert detail["turns"][0]["actor"] == "user"
        assert detail["turns"][1]["actor"] == "agent"

        # Step 6: Check for failures (slow LLM should be detected)
        failures_response = client.get("/failures")
        assert failures_response.status_code == 200
        failures = failures_response.json()

        # Should have at least one slow_response failure
        assert failures["count"] >= 1
        failure_types = [f["type"] for f in failures["failures"]]
        assert "slow_response" in failure_types

    def test_multiple_conversations_workflow(self, client):
        """Test handling multiple conversations simultaneously."""
        # Ingest spans for multiple conversations
        multi_conv_spans = {
            "spans": [
                # Conversation 1
                {
                    "name": "voice.turn",
                    "duration_ms": 1000.0,
                    "attributes": {
                        "voice.actor": "user",
                        "voice.conversation.id": "conv-multi-1",
                        "voice.turn.index": 0,
                    },
                },
                {
                    "name": "voice.turn",
                    "duration_ms": 1200.0,
                    "attributes": {
                        "voice.actor": "agent",
                        "voice.conversation.id": "conv-multi-1",
                        "voice.turn.index": 1,
                    },
                },
                # Conversation 2
                {
                    "name": "voice.turn",
                    "duration_ms": 800.0,
                    "attributes": {
                        "voice.actor": "user",
                        "voice.conversation.id": "conv-multi-2",
                        "voice.turn.index": 0,
                    },
                },
                {
                    "name": "voice.turn",
                    "duration_ms": 900.0,
                    "attributes": {
                        "voice.actor": "agent",
                        "voice.conversation.id": "conv-multi-2",
                        "voice.turn.index": 1,
                    },
                },
                # Conversation 3
                {
                    "name": "voice.turn",
                    "duration_ms": 1100.0,
                    "attributes": {
                        "voice.actor": "user",
                        "voice.conversation.id": "conv-multi-3",
                        "voice.turn.index": 0,
                    },
                },
            ]
        }

        # Ingest
        response = client.post("/ingest", json=multi_conv_spans)
        assert response.status_code == 201
        assert response.json()["accepted"] == 5

        # List conversations
        conv_list = client.get("/conversations")
        assert conv_list.status_code == 200
        convs = conv_list.json()
        assert convs["count"] == 3

        # Check each conversation
        conv_ids = [c["id"] for c in convs["conversations"]]
        assert "conv-multi-1" in conv_ids
        assert "conv-multi-2" in conv_ids
        assert "conv-multi-3" in conv_ids

        # Analyze shows correct totals
        analysis = client.get("/analyze").json()
        assert analysis["summary"]["total_conversations"] == 3
        assert analysis["summary"]["total_turns"] == 5

    def test_clear_and_reingest_workflow(self, client):
        """Test clearing data and reingesting."""
        # Initial ingest
        spans = {
            "spans": [
                {"name": "voice.turn", "duration_ms": 100.0, "attributes": {}},
                {"name": "voice.turn", "duration_ms": 200.0, "attributes": {}},
            ]
        }
        client.post("/ingest", json=spans)

        # Verify initial state
        assert client.get("/spans").json()["count"] == 2

        # Clear all spans
        clear_response = client.delete("/spans")
        assert clear_response.status_code == 200
        assert clear_response.json()["cleared"] == 2

        # Verify cleared
        assert client.get("/spans").json()["count"] == 0

        # Reingest
        new_spans = {
            "spans": [
                {"name": "voice.asr", "duration_ms": 150.0, "attributes": {}},
            ]
        }
        client.post("/ingest", json=new_spans)

        # Verify new state
        assert client.get("/spans").json()["count"] == 1

    def test_analysis_with_audio_metadata(self, client):
        """Test that audio metadata is preserved through the workflow."""
        # Ingest spans with audio metadata
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "duration_ms": 2500.0,
                    "attributes": {
                        "voice.actor": "user",
                        "voice.conversation.id": "audio-conv-1",
                        "voice.turn.id": "audio-turn-1",
                        "voice.turn.index": 0,
                        "voice.turn.audio_url": "s3://bucket/user-audio.wav",
                        "voice.turn.audio_duration_ms": 2400.0,
                        "voice.turn.audio_format": "wav",
                        "voice.turn.audio_sample_rate": 16000,
                        "voice.turn.audio_channels": 1,
                    },
                },
            ]
        }

        # Ingest
        response = client.post("/ingest", json=spans)
        assert response.status_code == 201
        span_id = response.json()["span_ids"][0]

        # Retrieve and verify audio metadata is preserved
        span_response = client.get(f"/spans/{span_id}")
        assert span_response.status_code == 200
        span_data = span_response.json()

        assert span_data["attributes"]["voice.turn.audio_url"] == "s3://bucket/user-audio.wav"
        assert span_data["attributes"]["voice.turn.audio_duration_ms"] == 2400.0
        assert span_data["attributes"]["voice.turn.audio_format"] == "wav"
        assert span_data["attributes"]["voice.turn.audio_sample_rate"] == 16000
        assert span_data["attributes"]["voice.turn.audio_channels"] == 1
