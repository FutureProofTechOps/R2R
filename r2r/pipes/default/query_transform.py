import logging
from typing import Any, AsyncGenerator, Optional

from r2r.core import (
    AsyncContext,
    AsyncPipe,
    GenerationConfig,
    LLMProvider,
    PipeFlow,
    PipeType,
    PromptProvider,
)

from ..abstractions.loggable import LoggableAsyncPipe

logger = logging.getLogger(__name__)


class DefaultQueryTransformPipe(LoggableAsyncPipe):
    class QueryTransformConfig(LoggableAsyncPipe.PipeConfig):
        name: str = "default_query_transform"
        num_answers: int = 3
        model: str = "gpt-3.5-turbo"
        system_prompt: str = "default_system_prompt"
        task_prompt: str = "hyde_prompt"
        generation_config: GenerationConfig = GenerationConfig(
            model="gpt-3.5-turbo"
        )

    def __init__(
        self,
        llm_provider: LLMProvider,
        prompt_provider: PromptProvider,
        flow: PipeFlow = PipeFlow.FAN_OUT,
        type: PipeType = PipeType.TRANSFORM,
        config: Optional[QueryTransformConfig] = None,
        *args,
        **kwargs,
    ):
        logger.info(f"Initalizing an `DefaultQueryTransformPipe` pipe.")
        super().__init__(
            flow=flow,
            type=type,
            config=config or DefaultQueryTransformPipe.QueryTransformConfig(),
            *args,
            **kwargs,
        )
        self.llm_provider = llm_provider
        self.prompt_provider = prompt_provider

    async def _run_logic(
        self,
        input: AsyncPipe.Input,
        context: AsyncContext,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncGenerator[Any, None]:
        for query in ["a", "b", "c"]:
            yield query
        # messages = self._get_llm_payload(input.message)

        # response = self.llm_provider.get_completion(
        #     messages=messages,
        #     generation_config=self.config.generation_config,
        # )
        # content = self.llm_provider.extract_content(response)
        # queries = content.split("\n\n")

        # await context.update(
        #     self.config.name, {"output": {"queries": queries}}
        # )

        # for query in queries:
        #     yield query

    def _get_llm_payload(self, input: str) -> dict:
        return [
            {
                "role": "system",
                "content": self.prompt_provider.get_prompt(
                    self.config.system_prompt,
                ),
            },
            {
                "role": "user",
                "content": self.prompt_provider.get_prompt(
                    self.config.task_prompt,
                    inputs={
                        "message": input,
                        "num_answers": self.config.num_answers,
                    },
                ),
            },
        ]
