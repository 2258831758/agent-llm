from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class SandboxSession:
    sandbox_id: str
    status: str
    message: str


class SandboxRunner(ABC):
    @abstractmethod
    async def create(self, task_id: str) -> SandboxSession:
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self, sandbox_id: str) -> None:
        raise NotImplementedError


class StubSandboxRunner(SandboxRunner):
    async def create(self, task_id: str) -> SandboxSession:
        return SandboxSession(
            sandbox_id=f"stub-{uuid4()}",
            status="not_implemented",
            message=f"任务 {task_id} 的沙箱接口已预留，当前使用占位实现。",
        )

    async def cleanup(self, sandbox_id: str) -> None:
        return None


_sandbox_runner: SandboxRunner = StubSandboxRunner()


def get_sandbox_runner() -> SandboxRunner:
    return _sandbox_runner
