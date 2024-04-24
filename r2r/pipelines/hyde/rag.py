import json
import logging
from typing import Generator, Optional

from r2r.core import (
    EmbeddingProvider,
    GenerationConfig,
    LLMProvider,
    LoggingDatabaseConnection,
    PromptProvider,
    RAGPipeline,
    RAGPipelineOutput,
    VectorDBProvider,
    VectorSearchResult,
    log_execution_to_db,
)

from ...prompts.local.prompt import BasicPromptProvider
from ..qna.rag import QnARAGPipeline

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."
DEFAULT_TASK_PROMPT = """
## Task:
Answer the query given immediately below given the context which follows later. Use line item references to like [1], [2], ... refer to specifically numbered items in the provided context. Pay close attention to the title of each given source to ensure it is consistent with the query.

### Query:
{query}

### Context:
{context}

### Query:
{query}

REMINDER - Use line item references to like [1], [2], ... refer to specifically numbered items in the provided context.
## Response:
"""
DEFAULT_HYDE_PROMPT = """
### Instruction:

Given the following query that follows to write a double newline separated list of up to {num_answers} single paragraph attempted answers. 
DO NOT generate any single answer which is likely to require information from multiple distinct documents, 
EACH single answer will be used to carry out a cosine similarity semantic search over distinct indexed documents, such as varied medical documents. 
FOR EXAMPLE if asked `how do the key themes of Great Gatsby compare with 1984`, the two attempted answers would be 
`The key themes of Great Gatsby are ... ANSWER_CONTINUED` and `The key themes themes of 1984 are ... ANSWER_CONTINUED`, where `ANSWER_CONTINUED` IS TO BE COMPLETED BY YOU in your response. 
Here is the original user query to be transformed into answers:

{query}

### Response:
"""


class HyDEPipeline(QnARAGPipeline):
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
        vector_db_provider: VectorDBProvider,
        prompt_provider: Optional[PromptProvider] = None,
        logging_connection: Optional[LoggingDatabaseConnection] = None,
        system_prompt: Optional[str] = DEFAULT_SYSTEM_PROMPT,
        task_prompt: Optional[str] = DEFAULT_TASK_PROMPT,
        hyde_prompt: Optional[str] = DEFAULT_HYDE_PROMPT,
    ) -> None:
        logger.debug(f"Initalizing `HydePipeline`")

        if not prompt_provider:
            prompt_provider = BasicPromptProvider
        self.prompt_provider = prompt_provider(system_prompt, task_prompt)
        self.prompt_provider.add_prompt("hyde_prompt", hyde_prompt)

        super().__init__(
            llm_provider=llm_provider,
            vector_db_provider=vector_db_provider,
            embedding_provider=embedding_provider,
            logging_connection=logging_connection,
            prompt_provider=self.prompt_provider,
        )

    def transform_query(self, query: str, generation_config: GenerationConfig) -> list[str]:  # type: ignore
        """
        Transforms the query into a list of hypothetical queries.
        """
        self._check_pipeline_initialized()
        orig_stream = generation_config.stream
        generation_config.stream = False

        num_answers = generation_config.add_generation_kwargs.get(
            "num_answers", "three"
        )

        formatted_prompt = self.prompt_provider.get_prompt(
            "hyde_prompt", {"query": query, "num_answers": num_answers}
        )

        completion = self.generate_completion(
            formatted_prompt, generation_config
        )
        transformed_queries = (
            completion.choices[0].message.content.strip().split("\n\n")
        )
        generation_config.stream = orig_stream
        return transformed_queries

    @log_execution_to_db
    def search(
        self,
        transformed_query: str,
        filters: dict,
        limit: int,
        *args,
        **kwargs,
    ) -> list[VectorSearchResult]:
        logger.debug(f"Retrieving results for query: {transformed_query}")

        results = self.vector_db_provider.search(
            query_vector=self.embedding_provider.get_embedding(
                transformed_query,
            ),
            filters=filters,
            limit=limit,
        )
        logger.debug(f"Retrieved the raw results shown:\n{results}\n")
        return results

    @log_execution_to_db
    def construct_context(
        self,
        results: list,
    ) -> str:
        queries = [ele[0] for ele in results]
        search_results = [ele[1] for ele in results]
        context = ""
        offset = 1
        for query, results in zip(queries, search_results):
            context += f"## Query:\n{query}\n\n## Context:\n{self._format_results(results, offset)}\n\n"
            offset += len(results)
        return context

    # Modifies `HydePipeline` run to return search_results and completion
    def run(
        self,
        query,
        filters={},
        search_limit=25,
        rerank_limit=15,
        search_only=False,
        generation_config: Optional[GenerationConfig] = None,
        *args,
        **kwargs,
    ):
        """
        Runs the completion pipeline.
        """
        if not generation_config:
            generation_config = GenerationConfig(model="gpt-3.5-turbo")

        self.initialize_pipeline(query, search_only)
        transformed_queries = self.transform_query(query, generation_config)
        search_results = [
            (
                transformed_query,
                self.rerank_results(
                    transformed_query,
                    self.search(transformed_query, filters, search_limit),
                    rerank_limit,
                ),
            )
            for transformed_query in transformed_queries
        ]
        if search_only:
            return RAGPipelineOutput(search_results, None, None)
        context = self.construct_context(search_results)
        prompt = self.construct_prompt({"query": query, "context": context})

        if not generation_config.stream:
            completion = self.generate_completion(prompt, generation_config)
            return RAGPipelineOutput(search_results, context, completion)

        return self._stream_run(
            search_results, context, prompt, generation_config
        )

    def _format_results(
        self, results: list[VectorSearchResult], start=1
    ) -> str:
        context = ""
        for i, ele in enumerate(results, start=start):
            context += f"[{i+start}] {ele.metadata['text']}\n\n"

        return context

    def _stream_run(
        self,
        search_results: list,
        context: str,
        prompt: str,
        generation_config: GenerationConfig,
    ) -> Generator[str, None, None]:
        yield f"<{RAGPipeline.SEARCH_STREAM_MARKER}>"
        yield json.dumps([ele[1][0].to_dict() for ele in search_results])
        yield f"</{RAGPipeline.SEARCH_STREAM_MARKER}>"

        yield f"<{RAGPipeline.CONTEXT_STREAM_MARKER}>"
        yield context
        yield f"</{RAGPipeline.CONTEXT_STREAM_MARKER}>"
        yield f"<{RAGPipeline.COMPLETION_STREAM_MARKER}>"
        for chunk in self.generate_completion(prompt, generation_config):
            yield chunk
        yield f"</{RAGPipeline.COMPLETION_STREAM_MARKER}>"
