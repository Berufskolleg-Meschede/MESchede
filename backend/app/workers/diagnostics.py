"""Read-only diagnostics for the in-process PLC workers."""

import asyncio
import logging
from dataclasses import dataclass


@dataclass
class WorkerDiagnostics:
    phase: str = "stopped"
    last_error: str | None = None
    last_order_id: str | None = None
    last_completed_order_id: str | None = None

    def snapshot(self, task: asyncio.Task | None, queue: asyncio.Queue, current_order_id: str | None):
        return {
            "worker_running": task is not None and not task.done(),
            "worker_phase": self.phase,
            "queue_size": queue.qsize(),
            "current_order_id": current_order_id,
            "last_order_id": self.last_order_id,
            "last_completed_order_id": self.last_completed_order_id,
            "last_error": self.last_error,
        }

    def task_finished(self, task: asyncio.Task, worker_name: str, logger: logging.Logger):
        if task.cancelled():
            self.phase = "stopped"
            logger.info("%s worker stopped (cancelled)", worker_name)
            return
        error = task.exception()
        if error is not None:
            self.phase = "failed"
            self.last_error = f"{type(error).__name__}: {error}"
            logger.error(
                "%s worker stopped unexpectedly", worker_name,
                exc_info=(type(error), error, error.__traceback__),
            )
        else:
            self.phase = "stopped"
            logger.info("%s worker stopped", worker_name)
