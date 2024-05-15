import argparse
import os

import uvicorn

from r2r import (
    DefaultR2RPipelineFactory,
    R2RApp,
    R2RConfig,
    R2RProviderFactory,
)

# from r2r.main import E2EPipeFactory, R2RConfig
# from r2r.pipes import AgentRAGPipe, HyDEPipe, QnARAGPipe, WebRAGPipe


current_file_path = os.path.dirname(__file__)
configs_path = os.path.join(current_file_path, "..", "configs")

CONFIG_OPTIONS = {
    "default": None,
    "local_ollama": os.path.join(configs_path, "local_ollama.json"),
    "local_ollama_qdrant": os.path.join(
        configs_path, "local_ollama_qdrant.json"
    ),
    "local_ollama_with_rerank": os.path.join(
        configs_path, "local_ollama_with_rerank.json"
    ),
    "local_llama_cpp": os.path.join(configs_path, "local_llama_cpp.json"),
}

# PIPELINE_OPTIONS = {
#     "qna": QnARAGPipe,
#     "web": WebRAGPipe,
#     "agent": AgentRAGPipe,
#     "hyde": HyDEPipe,
# }


def default_app(config_name: str = "default", pipe_name: str = "qna"):
    config_name = os.getenv("CONFIG_OPTION") or config_name
    pipe_name = os.getenv("PIPELINE_OPTION") or pipe_name

    # config_path = CONFIG_OPTIONS[config_name]
    # # pipe_impl = PIPELINE_OPTIONS[pipe_name]

    # app = DefaultR2RPipelineFactory.create_pipe(
    #     config=R2RConfig.from_json(config_path),
    #     rag_pipe_impl=pipe_impl,
    # )
    # return app
    config = R2RConfig.from_json()

    providers = R2RProviderFactory(config).create_providers()
    default_factory = DefaultR2RPipelineFactory(config, providers)
    default_factory.configure_logging()
    pipelines = default_factory.create_pipelines()

    r2r = R2RApp(
        config=config,
        ingestion_pipeline=pipelines.ingestion_pipeline,
        search_pipeline=pipelines.search_pipeline,
        rag_pipeline=pipelines.rag_pipeline,
        streaming_rag_pipeline=pipelines.streaming_rag_pipeline,
    )

    return r2r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="R2R Pipe")
    parser.add_argument(
        "--config",
        type=str,
        default="default",
        choices=CONFIG_OPTIONS.keys(),
        help="Configuration option for the pipe",
    )
    # parser.add_argument(
    #     "--pipe",
    #     type=str,
    #     default="qna",
    #     choices=PIPELINE_OPTIONS.keys(),
    #     help="Pipe implementation to be deployed",
    # )
    parser.add_argument(
        "--port",
        type=str,
        default="8000",
        help="Port to serve deployed pipe on.",
    )

    args, _ = parser.parse_known_args()

    port = os.getenv("PORT") or args.port

    app = default_app(args.config)  # , args.pipe)
    app.serve(host="0.0.0.0", port=int(port))
