"""Tests for worker CLI entry point."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.workers.cli import start_worker


class TestWorkerCli:
    """Tests for worker CLI."""

    def test_start_worker_exits_when_execution_queue_not_configured(self):
        """Test start_worker exits when execution queue not configured."""
        with (
            patch(
                "voiceobs.server.dependencies.init_database",
                new_callable=AsyncMock,
            ),
            patch(
                "voiceobs.server.dependencies.get_execution_queue_client",
                return_value=None,
            ),
            patch("voiceobs.server.workers.cli.sys.exit", side_effect=SystemExit(1)),
        ):
            with pytest.raises(SystemExit):
                start_worker()

    def test_start_worker_exits_when_evaluation_queue_not_configured(self):
        """Test start_worker exits when evaluation queue not configured."""
        with (
            patch(
                "voiceobs.server.dependencies.init_database",
                new_callable=AsyncMock,
            ),
            patch(
                "voiceobs.server.dependencies.get_execution_queue_client",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_evaluation_queue_client",
                return_value=None,
            ),
            patch("voiceobs.server.workers.cli.sys.exit", side_effect=SystemExit(1)),
        ):
            with pytest.raises(SystemExit):
                start_worker()

    def test_start_worker_exits_when_evaluation_service_not_available(self):
        """Test start_worker exits when evaluation service not available."""
        with (
            patch(
                "voiceobs.server.dependencies.init_database",
                new_callable=AsyncMock,
            ),
            patch(
                "voiceobs.server.dependencies.get_execution_queue_client",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_evaluation_queue_client",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_evaluation_service",
                return_value=None,
            ),
            patch("voiceobs.server.workers.cli.sys.exit", side_effect=SystemExit(1)),
        ):
            with pytest.raises(SystemExit):
                start_worker()

    def test_start_worker_exits_when_scenario_call_service_not_available(self):
        """Test start_worker exits when ScenarioCallService not available."""
        with (
            patch(
                "voiceobs.server.dependencies.init_database",
                new_callable=AsyncMock,
            ),
            patch(
                "voiceobs.server.dependencies.get_execution_queue_client",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_evaluation_queue_client",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_evaluation_service",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_scenario_call_service",
                return_value=None,
            ),
            patch("voiceobs.server.workers.cli.sys.exit", side_effect=SystemExit(1)),
        ):
            with pytest.raises(SystemExit):
                start_worker()

    def test_start_worker_creates_workers_with_env_concurrency(self):
        """Test start_worker creates workers with concurrency from env."""
        mock_call_worker = MagicMock()
        mock_eval_worker = MagicMock()
        mock_call_worker.poll_loop = AsyncMock(return_value=None)
        mock_eval_worker.poll_loop = AsyncMock(return_value=None)

        with (
            patch(
                "voiceobs.server.dependencies.init_database",
                new_callable=AsyncMock,
            ),
            patch(
                "voiceobs.server.dependencies.get_execution_queue_client",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_evaluation_queue_client",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_evaluation_service",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_scenario_call_service",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_test_execution_repository",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.dependencies.get_test_suite_run_repository",
                return_value=MagicMock(),
            ),
            patch(
                "voiceobs.server.workers.call_worker.CallWorker",
                return_value=mock_call_worker,
            ) as call_worker_mock,
            patch(
                "voiceobs.server.workers.eval_worker.EvalWorker",
                return_value=mock_eval_worker,
            ) as eval_worker_mock,
            patch.dict(
                "os.environ",
                {
                    "VOICEOBS_WORKER_CALL_CONCURRENCY": "5",
                    "VOICEOBS_WORKER_EVAL_CONCURRENCY": "15",
                },
                clear=False,
            ),
        ):
            start_worker()

        call_worker_mock.assert_called_once()
        call_kwargs = call_worker_mock.call_args[1]
        assert call_kwargs["concurrency"] == 5

        eval_worker_mock.assert_called_once()
        eval_kwargs = eval_worker_mock.call_args[1]
        assert eval_kwargs["concurrency"] == 15
