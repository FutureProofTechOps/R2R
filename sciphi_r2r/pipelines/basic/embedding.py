"""
A simple example to demonstrate the usage of `BasicEmbeddingPipeline`.
"""
import copy
import logging
import uuid
from typing import Any, Optional, Tuple, Union

from langchain.text_splitter import TextSplitter
from pydantic import BaseModel

from sciphi_r2r.core import (
    EmbeddingPipeline,
    LoggingDatabaseConnection,
    VectorDBProvider,
    VectorEntry,
)
from sciphi_r2r.embeddings import OpenAIEmbeddingProvider

logger = logging.getLogger(__name__)


class BasicDocument(BaseModel):
    id: str
    text: str
    metadata: dict


class BasicEmbeddingPipeline(EmbeddingPipeline):
    def __init__(
        self,
        embedding_model: str,
        embeddings_provider: OpenAIEmbeddingProvider,
        db: VectorDBProvider,
        text_splitter: TextSplitter,
        logging_database: Optional[LoggingDatabaseConnection] = None,
        embedding_batch_size: int = 1,
        id_prefix: str = "demo",
    ):
        logger.info(
            f"Initalizing a `BasicEmbeddingPipeline` to embed and store documents."
        )

        super().__init__(
            embedding_model,
            embeddings_provider,
            db,
            logging_database,
        )
        self.text_splitter = text_splitter
        self.embedding_batch_size = embedding_batch_size
        self.id_prefix = id_prefix

    def extract_text(self, document: Any) -> str:
        return next(document)[0]

    def transform_text(self, text: str) -> str:
        return text

    def chunk_text(self, text: str) -> list[str]:
        return [
            ele.page_content
            for ele in self.text_splitter.create_documents([text])
        ]

    def transform_chunks(
        self, chunks: list[str], metadata: list[dict]
    ) -> list[str]:
        return chunks

    def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        return self.embeddings_provider.get_embeddings(
            chunks, self.embedding_model
        )

    def store_chunks(self, chunks: list[VectorEntry]) -> None:
        self.db.upsert_entries(chunks)

    def process_batches(self, batch_data: list[Tuple[str, int, str, dict]]):
        logger.debug(f"Parsing batch of size {len(batch_data)}.")

        entries = []

        # Unpack document IDs, indices, and chunks for transformation and embedding
        doc_ids, indices, raw_chunks, metadata = zip(*batch_data)
        transformed_chunks = self.transform_chunks(raw_chunks, metadata)
        embedded_chunks = self.embed_chunks(transformed_chunks)  # Batch embed

        for doc_id, i, original_chunk, embedded_chunk, metadatas in zip(
            doc_ids, indices, raw_chunks, embedded_chunks, metadata
        ):
            chunk_id = uuid.uuid4()
            metadatas = copy.deepcopy(metadatas)
            metadatas["doc_id"] = str(doc_id)
            metadatas["pipeline_run_id"] = str(self.pipeline_run_id)
            metadatas["text"] = original_chunk
            entries.append(VectorEntry(chunk_id, embedded_chunk, metadatas))
        self.store_chunks(entries)

    def run(
        self,
        document: Union[BasicDocument, list[BasicDocument]],
        chunk_text=False,
        **kwargs: Any,
    ):
        self.pipeline_run_id = uuid.uuid4()
        logger.debug(
            f"Running the `BasicEmbeddingPipeline` with id={self.pipeline_run_id}."
        )

        documents = [document] if not isinstance(document, list) else document
        batch_data = []

        for document in documents:
            chunks = self.chunk_text(document.text)
            for i, chunk in enumerate(chunks):
                batch_data.append((document.id, i, chunk, document.metadata))

                if len(batch_data) == self.embedding_batch_size or (
                    document == documents[-1] and i == len(chunks) - 1
                ):
                    self.process_batches(batch_data)
                    batch_data = []

        # Process any remaining batch
        if batch_data:
            self.process_batches(batch_data)
