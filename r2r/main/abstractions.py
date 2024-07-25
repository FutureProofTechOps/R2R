from typing import Optional

from pydantic import BaseModel

from r2r.base import (
    AsyncPipe,
    AuthProvider,
    DatabaseProvider,
    EmbeddingProvider,
    EvalProvider,
    KGProvider,
    LLMProvider,
    PromptProvider,
)
from r2r.pipelines import (
    EvalPipeline,
    IngestionPipeline,
    RAGPipeline,
    SearchPipeline,
    KGEntityMergingPipeline
)


class R2RProviders(BaseModel):
    auth: Optional[AuthProvider]
    database: Optional[DatabaseProvider]
    embedding: Optional[EmbeddingProvider]
    llm: Optional[LLMProvider]
    prompt: Optional[PromptProvider]
    eval: Optional[EvalProvider]
    kg: Optional[KGProvider]

    class Config:
        arbitrary_types_allowed = True


class R2RPipes(BaseModel):
    parsing_pipe: Optional[AsyncPipe]
    embedding_pipe: Optional[AsyncPipe]
    vector_storage_pipe: Optional[AsyncPipe]
    vector_search_pipe: Optional[AsyncPipe]
    rag_pipe: Optional[AsyncPipe]
    streaming_rag_pipe: Optional[AsyncPipe]
    eval_pipe: Optional[AsyncPipe]
    kg_pipe: Optional[AsyncPipe]
    kg_storage_pipe: Optional[AsyncPipe]
    kg_agent_search_pipe: Optional[AsyncPipe]
    kg_entity_merging_pipe: Optional[AsyncPipe]

    class Config:
        arbitrary_types_allowed = True


class R2RPipelines(BaseModel):
    eval_pipeline: EvalPipeline
    ingestion_pipeline: IngestionPipeline
    search_pipeline: SearchPipeline
    rag_pipeline: RAGPipeline
    streaming_rag_pipeline: RAGPipeline
    kg_entity_merging_pipeline: KGEntityMergingPipeline

    class Config:
        arbitrary_types_allowed = True
