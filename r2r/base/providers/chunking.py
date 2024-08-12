from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncGenerator, List, Optional

from pydantic import BaseModel, Field

from ..abstractions.document import Document, DocumentType
from .base import Provider, ProviderConfig


class Method(str, Enum):
    BY_TITLE = "by_title"
    BASIC = "basic"
    RECURSIVE = "recursive"


class ChunkingConfig(ProviderConfig):
    provider: str = "r2r"
    method: Method = Method.RECURSIVE
    chunk_size: int = 512
    chunk_overlap: int = 20
    max_chunk_size: Optional[int] = None

    def validate(self) -> None:
        if self.provider not in self.supported_providers:
            raise ValueError(f"Provider {self.provider} is not supported.")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")

    @property
    def supported_providers(self) -> list[str]:
        return ["r2r", "unstructured", None]


class ChunkingProvider(Provider, ABC):
    def __init__(self, config: ChunkingConfig):
        super().__init__(config)
        self.config = config

    @abstractmethod
    async def chunk(self, parsed_document: str) -> AsyncGenerator[str, None]:
        """Chunk the parsed document using the configured chunking strategy."""
        pass
