import asyncio
import uuid
from enum import Enum
from typing import Any, Optional, AsyncGenerator

from ..pipes.base import AsyncPipe, AsyncState, PipeFlow
from ..pipes.logging import PipeLoggingConnectionSingleton
from ..utils import generate_run_id


class PipelineTypes(Enum):
    INGESTION = "ingestion"
    SEARCH = "search"
    RAG = "rag"


class Pipeline:
    def __init__(
        self, pipe_logger: Optional[PipeLoggingConnectionSingleton] = None
    ):
        self.pipes: list[AsyncPipe] = []
        self.upstream_outputs: list[list[dict[str, str]]] = []
        self.pipe_logger = pipe_logger or PipeLoggingConnectionSingleton()
        self.futures = {}
        self.level = 0

    def add_pipe(
        self,
        pipe: AsyncPipe,
        add_upstream_outputs: Optional[list[dict[str, str]]] = None,
        *args,
        **kwargs,
    ) -> None:
        self.futures[pipe.config.name] = asyncio.Future()
        self.pipes.append(pipe)
        if not add_upstream_outputs:
            add_upstream_outputs = []
        self.upstream_outputs.append(add_upstream_outputs)

    async def run(
        self,
        input: Any,
        state: Optional[AsyncState] = None,
        pipeline_type: str = "ingestion",
    ):
        try:
            PipelineTypes(pipeline_type)
        except ValueError:
            raise ValueError(
                f"Invalid pipeline type: {pipeline_type}, must be one of {PipelineTypes.__members__.keys()}"
            )

        self.state = state or AsyncState()
        current_input = input
        run_id = generate_run_id()
        print(f"Running pipeline with run_id: {run_id}")
        await self.pipe_logger.log(
            pipe_run_id=run_id,
            key="pipeline_type",
            value=pipeline_type,
            is_pipeline_info=True,
        )

        for pipe_num in range(len(self.pipes)):
            if self.pipes[pipe_num].flow == PipeFlow.FAN_OUT:
                if self.level == 0:
                    current_input = self._run_pipe(
                        pipe_num, current_input, run_id
                    )
                    self.level += 1
                elif self.level == 1:
                    raise ValueError("Fan out not supported at level 1")
            elif self.pipes[pipe_num].flow == PipeFlow.STANDARD:
                if self.level == 0:
                    current_input = self._run_pipe(
                        pipe_num, current_input, run_id
                    )
                elif self.level == 1:
                    input = []
                    async for item in current_input:
                        if hasattr(item, "__aiter__"):
                            # extend the current input if the item is a generator
                            input.extend(
                                self._run_pipe(pipe_num, item, run_id)
                            )
                        else:
                            # otherwise, construct a generator from the item
                            input.append(
                                self._run_pipe(
                                    pipe_num,
                                    self._list_to_generator(item),
                                    run_id,
                                )
                            )
                    current_input = input
            elif self.pipes[pipe_num].flow == PipeFlow.FAN_IN:
                if self.level == 0:
                    raise ValueError("Fan in not supported at level 0")
                if self.level == 1:
                    current_input = self._run_pipe(
                        pipe_num,
                        self._list_to_generator(current_input),
                        run_id,
                    )
                    self.level -= 1
            self.futures[self.pipes[pipe_num].config.name].set_result(
                current_input
            )

        final_result = await self._consume_all(current_input)
        return final_result if len(final_result) > 1 else final_result[0]

    async def _consume_all(self, gen: AsyncGenerator) -> list[Any]:
        result = []
        async for item in gen:
            if hasattr(
                item, "__aiter__"
            ):  # Check if the item is an async generator
                sub_result = await self._consume_all(item)
                result.extend(sub_result)
            else:
                result.append(item)
        return result

    async def _list_to_generator(self, lst: list) -> AsyncGenerator:
        for item in lst:
            yield item

    async def _run_pipe(self, pipe_num: int, input: Any, run_id: uuid.UUID):
        # Collect inputs, waiting for the necessary futures
        pipe = self.pipes[pipe_num]
        add_upstream_outputs = self.upstream_outputs[pipe_num]
        input_dict = {"message": input}
        print("running pipe = ", pipe)
        for upstream_input in add_upstream_outputs:
            upstream_pipe_name = upstream_input["prev_pipe_name"]

            async def resolve_future_output(future):
                result = future.result()
                # consume the async generator
                return [item async for item in result]

            async def replay_items_as_async_gen(items):
                for item in items:
                    yield item

            temp_results = await resolve_future_output(
                self.futures[upstream_pipe_name]
            )
            if upstream_pipe_name == self.pipes[pipe_num - 1].config.name:
                input_dict["message"] = replay_items_as_async_gen(temp_results)

            outputs = await self.state.get(
                upstream_input["prev_pipe_name"], "output"
            )
            prev_output_field = upstream_input.get("prev_output_field", None)
            if not prev_output_field:
                raise ValueError(
                    "`prev_output_field` must be specified in the upstream_input"
                )
            input_dict[upstream_input["input_field"]] = outputs[
                upstream_input["prev_output_field"]
            ]

        # Handle the pipe generator
        async for ele in await pipe.run(
            pipe.Input(**input_dict), self.state, run_id=run_id
        ):
            yield ele
