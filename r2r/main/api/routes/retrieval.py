from typing import Optional

from fastapi import Depends
from fastapi.responses import StreamingResponse

from r2r.base import GenerationConfig, KGSearchSettings, VectorSearchSettings

from ...engine import R2REngine
from ..requests import R2REvalRequest, R2RRAGRequest, R2RSearchRequest
from .base_router import BaseRouter


class RetrievalRouter(BaseRouter):
    def __init__(
        self, engine: R2REngine
    ):
        super().__init__(engine)
        self.setup_routes()

    def setup_routes(self):
        @self.router.post("/search")
        @self.base_endpoint
        async def search_app(
            request: R2RSearchRequest,
            auth_user=(
                Depends(self.engine.auth_provider.auth_wrapper)
                if self.engine.config.auth.get("enabled")
                else None
            ),
        ):
            results = await self.engine.asearch(
                query=request.query,
                vector_search_settings=request.vector_search_settings
                or VectorSearchSettings(),
                kg_search_settings=request.kg_search_settings
                or KGSearchSettings(),
            )
            return results

        @self.router.post("/rag")
        @self.base_endpoint
        async def rag_app(
            request: R2RRAGRequest,
            auth_user=(
                Depends(self.engine.auth_provider.auth_wrapper)
                if self.engine.config.auth.get("enabled")
                else None
            ),
        ):
            response = await self.engine.arag(
                query=request.query,
                vector_search_settings=request.vector_search_settings
                or VectorSearchSettings(),
                kg_search_settings=request.kg_search_settings
                or KGSearchSettings(),
                rag_generation_config=request.rag_generation_config
                or GenerationConfig(),
            )

            if (
                request.rag_generation_config
                and request.rag_generation_config.stream
            ):

                async def stream_generator():
                    async for chunk in response:
                        yield chunk

                return StreamingResponse(
                    stream_generator(), media_type="application/json"
                )
            else:
                return response

        @self.router.post("/evaluate")
        @self.base_endpoint
        async def evaluate_app(
            request: R2REvalRequest,
            auth_user=(
                Depends(self.engine.auth_provider.auth_wrapper)
                if self.engine.config.auth.get("enabled")
                else None
            ),
        ):
            results = await self.engine.aevaluate(
                query=request.query,
                context=request.context,
                completion=request.completion,
            )
            return results
