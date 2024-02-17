import logging
import os
from typing import Any, Optional

from sciphi_r2r.core import VectorDBProvider, VectorEntry, VectorSearchResult
from sciphi_r2r.vecs.client import Client
from sciphi_r2r.vecs.collection import Collection

logger = logging.getLogger(__name__)


class PGVectorDB(VectorDBProvider):
    def __init__(self, provider: str = "pgvector") -> None:
        logger.info(
            "Initializing `PGVectorDB` to store and retrieve embeddings."
        )

        super().__init__(provider)
        if provider != "pgvector":
            raise ValueError(
                "PGVectorDB must be initialized with provider `pgvector`."
            )
        try:
            import sciphi_r2r.vecs
        except ImportError:
            raise ValueError(
                f"Error, PGVectorDB requires the vecs library. Please run `poetry add vecs`."
            )
        try:
            user = os.getenv("PGVECTOR_USER")
            password = os.getenv("PGVECTOR_PASSWORD")
            host = os.getenv("PGVECTOR_HOST")
            port = os.getenv("PGVECTOR_PORT")
            db_name = os.getenv("PGVECTOR_DBNAME")

            DB_CONNECTION = (
                f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            )
            self.vx: Client = sciphi_r2r.vecs.create_client(DB_CONNECTION)
        except Exception as e:
            raise ValueError(
                f"Error {e} occurred while attempting to connect to the pgvector provider with {DB_CONNECTION}."
            )
        self.collection: Optional[Collection] = None

    def initialize_collection(
        self, collection_name: str, dimension: float
    ) -> None:
        self.collection = self.vx.get_or_create_collection(
            name=collection_name, dimension=dimension
        )

    def upsert(self, entry: VectorEntry, commit=True) -> None:
        if self.collection is None:
            raise ValueError(
                "Please call `initialize_collection` before attempting to run `upsert`."
            )

        self.collection.upsert(
            records=[(entry.id, entry.vector, entry.metadata)]
        )

    def upsert_entries(self, entries: list[VectorEntry]) -> None:
        if self.collection is None:
            raise ValueError(
                "Please call `initialize_collection` before attempting to run `upsert_entries`."
            )

        self.collection.upsert(
            records=[
                (entry.id, entry.vector, entry.metadata) for entry in entries
            ]
        )

    def search(
        self,
        query_vector: list[float],
        filters: dict[str, Any] = {},
        limit: int = 10,
        **kwargs,
    ) -> list[VectorSearchResult]:
        if self.collection is None:
            raise ValueError(
                "Please call `initialize_collection` before attempting to run `search`."
            )
        measure = kwargs.get("measure", "cosine_distance")

        return [
            VectorSearchResult(ele[0], 1 - ele[1], ele[2])
            for ele in self.collection.query(
                data=query_vector,
                limit=limit,
                filters=filters,
                measure=measure,
                include_value=True,
                include_metadata=True,
            )
        ]

    def create_index(self, index_type, column_name, index_options):
        pass

    def close(self):
        pass
