from abc import ABC, abstractmethod
from typing import Any

from app.models.finding import Finding


class Analyzer(ABC):
    name: str = "base"

    @abstractmethod
    def analyze(self, source: str, filename: str) -> tuple[list[Finding], dict[str, Any]]:
        raise NotImplementedError
