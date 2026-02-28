"""Worker CLI entry point for call and eval workers."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from voiceobs.server.workers.call_worker import CallWorker
    from voiceobs.server.workers.eval_worker import EvalWorker


def _load_dotenv() -> None:
    """Load .env file if dotenv is available."""
    try:
        from dotenv import load_dotenv

        # Try cwd first, then project root (for dev)
        for path in [Path.cwd(), Path.cwd().parent]:
            env_path = path / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=False)
                break
        else:
            load_dotenv(override=False)
    except ImportError:
        pass


async def _run_workers(call_worker: CallWorker, eval_worker: EvalWorker) -> None:
    """Run call and eval workers concurrently."""
    await asyncio.gather(
        call_worker.poll_loop(),
        eval_worker.poll_loop(),
    )


def start_worker() -> None:
    """Start the worker process with both call and eval workers."""
    _load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    from voiceobs.server.dependencies import (
        get_evaluation_queue_client,
        get_evaluation_service,
        get_execution_queue_client,
        get_scenario_call_service,
        get_test_execution_repository,
        get_test_suite_run_repository,
        init_database,
    )
    from voiceobs.server.workers.call_worker import CallWorker
    from voiceobs.server.workers.eval_worker import EvalWorker

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    call_worker: CallWorker | None = None
    eval_worker: EvalWorker | None = None

    def shutdown(sig: signal.Signals | int | None = None) -> None:
        logger.info("Received signal %s, shutting down", sig)
        if call_worker is not None:
            call_worker._stop = True
        if eval_worker is not None:
            eval_worker._stop = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: shutdown(s))
        except NotImplementedError:
            pass

    async def main() -> None:
        nonlocal call_worker, eval_worker

        await init_database()

        execution_client = get_execution_queue_client()
        if execution_client is None:
            logger.error("VOICEOBS_SQS_EXECUTION_QUEUE_URL not set. Worker cannot start.")
            sys.exit(1)

        evaluation_client = get_evaluation_queue_client()
        if evaluation_client is None:
            logger.error("VOICEOBS_SQS_EVALUATION_QUEUE_URL not set. Worker cannot start.")
            sys.exit(1)

        evaluation_service = get_evaluation_service()
        if evaluation_service is None:
            logger.error("EvaluationService unavailable (LLM not configured). Worker cannot start.")
            sys.exit(1)

        scenario_call_service = get_scenario_call_service()
        if scenario_call_service is None:
            logger.error(
                "ScenarioCallService unavailable. "
                "Requires LiveKit (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, "
                "SIP_OUTBOUND_TRUNK_ID) and Egress S3 (VOICEOBS_AUDIO_STORAGE_PROVIDER=s3, "
                "VOICEOBS_AUDIO_STORAGE_PATH, VOICEOBS_AUDIO_S3_ACCESS_KEY/SECRET or "
                "AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY). Worker cannot start."
            )
            sys.exit(1)

        execution_repo = get_test_execution_repository()
        suite_run_repo = get_test_suite_run_repository()

        call_concurrency = int(os.environ.get("VOICEOBS_WORKER_CALL_CONCURRENCY", "10"))
        eval_concurrency = int(os.environ.get("VOICEOBS_WORKER_EVAL_CONCURRENCY", "20"))

        call_worker = CallWorker(
            execution_client=execution_client,
            evaluation_client=evaluation_client,
            scenario_call_service=scenario_call_service,
            concurrency=call_concurrency,
        )
        eval_worker = EvalWorker(
            evaluation_client=evaluation_client,
            execution_repo=execution_repo,
            suite_run_repo=suite_run_repo,
            evaluation_service=evaluation_service,
            concurrency=eval_concurrency,
        )

        logger.info(
            "Starting workers: call_concurrency=%d, eval_concurrency=%d",
            call_concurrency,
            eval_concurrency,
        )

        await _run_workers(call_worker, eval_worker)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        shutdown()
    finally:
        loop.close()
