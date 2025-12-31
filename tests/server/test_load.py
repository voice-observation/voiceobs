"""Load tests for the voiceobs server.

Tests server performance under load conditions.
"""

import concurrent.futures
import time


class TestLoadIngestion:
    """Tests for high-volume span ingestion."""

    def test_ingest_1000_spans_batch(self, client):
        """Test ingesting 1000 spans in a single batch."""
        # Generate 1000 spans
        spans = []
        for i in range(1000):
            spans.append(
                {
                    "name": "voice.turn",
                    "duration_ms": 100.0 + (i % 100),
                    "attributes": {
                        "voice.actor": "user" if i % 2 == 0 else "agent",
                        "voice.conversation.id": f"load-conv-{i // 10}",
                        "voice.turn.index": i % 10,
                    },
                }
            )

        # Measure ingestion time
        start_time = time.time()
        response = client.post("/ingest", json={"spans": spans})
        elapsed_time = time.time() - start_time

        assert response.status_code == 201
        assert response.json()["accepted"] == 1000

        # Should complete in reasonable time (< 5 seconds for in-memory storage)
        assert elapsed_time < 5.0, f"Ingestion took {elapsed_time:.2f}s, expected < 5s"

        # Verify all spans were stored
        spans_response = client.get("/spans")
        assert spans_response.json()["count"] == 1000

    def test_ingest_spans_in_batches(self, client):
        """Test ingesting spans in multiple smaller batches."""
        total_spans = 500
        batch_size = 50
        num_batches = total_spans // batch_size

        start_time = time.time()

        for batch_num in range(num_batches):
            spans = []
            for i in range(batch_size):
                spans.append(
                    {
                        "name": "voice.turn",
                        "duration_ms": 100.0,
                        "attributes": {
                            "voice.actor": "user",
                            "voice.conversation.id": f"batch-conv-{batch_num}",
                            "voice.turn.index": i,
                        },
                    }
                )
            response = client.post("/ingest", json={"spans": spans})
            assert response.status_code == 201
            assert response.json()["accepted"] == batch_size

        elapsed_time = time.time() - start_time

        # Verify total count
        spans_response = client.get("/spans")
        assert spans_response.json()["count"] == total_spans

        # Should complete in reasonable time
        assert elapsed_time < 10.0, f"Batch ingestion took {elapsed_time:.2f}s"

    def test_analyze_large_dataset(self, client):
        """Test analyzing a large number of spans."""
        # Ingest many spans with varied data
        spans = []
        for i in range(500):
            conv_id = f"analyze-conv-{i // 20}"
            spans.append(
                {
                    "name": "voice.turn",
                    "duration_ms": 500.0 + (i % 200),
                    "attributes": {
                        "voice.actor": "user" if i % 2 == 0 else "agent",
                        "voice.conversation.id": conv_id,
                        "voice.turn.index": i % 20,
                    },
                }
            )
            # Add stage spans
            if i % 4 == 0:
                spans.append(
                    {
                        "name": "voice.asr",
                        "duration_ms": 100.0 + (i % 50),
                        "attributes": {"voice.stage.type": "asr"},
                    }
                )
            if i % 4 == 1:
                spans.append(
                    {
                        "name": "voice.llm",
                        "duration_ms": 200.0 + (i % 100),
                        "attributes": {"voice.stage.type": "llm"},
                    }
                )
            if i % 4 == 2:
                spans.append(
                    {
                        "name": "voice.tts",
                        "duration_ms": 80.0 + (i % 40),
                        "attributes": {"voice.stage.type": "tts"},
                    }
                )

        # Ingest all spans
        client.post("/ingest", json={"spans": spans})

        # Measure analysis time
        start_time = time.time()
        response = client.get("/analyze")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        analysis = response.json()

        # Verify analysis results
        assert analysis["summary"]["total_spans"] > 500
        assert analysis["summary"]["total_conversations"] == 25  # 500 / 20

        # Should complete quickly
        assert elapsed_time < 2.0, f"Analysis took {elapsed_time:.2f}s"


class TestConcurrentRequests:
    """Tests for handling concurrent requests."""

    def test_concurrent_ingestion(self, client):
        """Test concurrent span ingestion requests."""
        num_threads = 10
        spans_per_thread = 50
        results = []

        def ingest_spans(thread_id: int) -> dict:
            spans = []
            for i in range(spans_per_thread):
                spans.append(
                    {
                        "name": "voice.turn",
                        "duration_ms": 100.0,
                        "attributes": {
                            "voice.conversation.id": f"concurrent-{thread_id}",
                            "voice.turn.index": i,
                        },
                    }
                )
            response = client.post("/ingest", json={"spans": spans})
            return {"status": response.status_code, "accepted": response.json().get("accepted", 0)}

        # Execute concurrent ingestion
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(ingest_spans, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed_time = time.time() - start_time

        # All requests should succeed
        for result in results:
            assert result["status"] == 201
            assert result["accepted"] == spans_per_thread

        # Verify total spans
        total_expected = num_threads * spans_per_thread
        spans_response = client.get("/spans")
        assert spans_response.json()["count"] == total_expected

        # Should handle concurrent requests efficiently
        assert elapsed_time < 5.0, f"Concurrent ingestion took {elapsed_time:.2f}s"

    def test_concurrent_read_operations(self, client):
        """Test concurrent read operations (analyze, list spans, etc.)."""
        # First, ingest some data
        spans = []
        for i in range(100):
            spans.append(
                {
                    "name": "voice.turn",
                    "duration_ms": 100.0,
                    "attributes": {
                        "voice.conversation.id": f"read-conv-{i // 10}",
                        "voice.turn.index": i % 10,
                    },
                }
            )
        client.post("/ingest", json={"spans": spans})

        num_threads = 20
        results = []

        def read_operation(thread_id: int) -> dict:
            # Mix of different read operations
            if thread_id % 4 == 0:
                response = client.get("/analyze")
            elif thread_id % 4 == 1:
                response = client.get("/spans")
            elif thread_id % 4 == 2:
                response = client.get("/conversations")
            else:
                response = client.get("/failures")
            return {"status": response.status_code, "thread": thread_id}

        # Execute concurrent reads
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(read_operation, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed_time = time.time() - start_time

        # All requests should succeed
        for result in results:
            assert result["status"] == 200

        # Should handle concurrent reads efficiently
        assert elapsed_time < 3.0, f"Concurrent reads took {elapsed_time:.2f}s"

    def test_concurrent_mixed_operations(self, client):
        """Test concurrent mix of read and write operations."""
        num_threads = 15
        results = []

        def mixed_operation(thread_id: int) -> dict:
            if thread_id % 3 == 0:
                # Write operation
                spans = [
                    {
                        "name": "voice.turn",
                        "duration_ms": 100.0,
                        "attributes": {"voice.conversation.id": f"mixed-{thread_id}"},
                    }
                ]
                response = client.post("/ingest", json={"spans": spans})
                return {"type": "write", "status": response.status_code}
            elif thread_id % 3 == 1:
                # Analyze operation
                response = client.get("/analyze")
                return {"type": "analyze", "status": response.status_code}
            else:
                # List operation
                response = client.get("/spans")
                return {"type": "list", "status": response.status_code}

        # Execute concurrent mixed operations
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(mixed_operation, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed_time = time.time() - start_time

        # Check results
        write_results = [r for r in results if r["type"] == "write"]
        read_results = [r for r in results if r["type"] in ("analyze", "list")]

        for result in write_results:
            assert result["status"] == 201
        for result in read_results:
            assert result["status"] == 200

        # Should complete in reasonable time
        assert elapsed_time < 5.0, f"Mixed operations took {elapsed_time:.2f}s"
