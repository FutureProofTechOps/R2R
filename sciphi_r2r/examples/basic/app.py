import os
import json
import logging

import dotenv
import uvicorn
from langchain.text_splitter import RecursiveCharacterTextSplitter

from sciphi_r2r.core import GenerationConfig, LoggingDatabaseConnection
from sciphi_r2r.datasets import HuggingFaceDataProvider
from sciphi_r2r.embeddings import OpenAIEmbeddingProvider
from sciphi_r2r.llms import OpenAIConfig, OpenAILLM
from sciphi_r2r.main import create_app
from sciphi_r2r.pipelines import BasicEmbeddingPipeline, BasicRAGPipeline
from sciphi_r2r.vector_dbs import PGVectorDB

if __name__ == "__main__":
    dotenv.load_dotenv()

    # Load configuration from JSON file
    execution_file_path = os.path.dirname(os.path.abspath(__file__))
    with open(
        os.path.join(
            execution_file_path, "..", "..", "..", "config.json"
        )
    ) as f:
        config = json.load(f)

    # Extract configuration parameters
    logging_config = config["logging"]
    embedding_config = config["embedding"]
    database_config = config["database"]
    language_model_config = config["language_model"]
    text_splitter_config = config["text_splitter"]

    logger = logging.getLogger(logging_config["name"])
    logging.basicConfig(level=logging_config["level"])

    logger.debug("Starting the completion pipeline")

    logger.debug("Using `OpenAIEmbeddingProvider` to provide embeddings.")
    embeddings_provider = OpenAIEmbeddingProvider()
    embedding_model = embedding_config["model"]
    embedding_dimension = embedding_config["dimension"]

    logger.debug("Using `PGVectorDB` to store and retrieve embeddings.")
    db = PGVectorDB()
    collection_name = database_config["collection_name"]
    db.initialize_collection(collection_name, embedding_dimension)

    logger.debug("Using `OpenAILLM` to provide language models.")
    llm = OpenAILLM(OpenAIConfig())
    generation_config = GenerationConfig(
        model_name=language_model_config["model_name"],
        temperature=language_model_config["temperature"],
        top_p=language_model_config["top_p"],
        top_k=language_model_config["top_k"],
        max_tokens_to_sample=language_model_config["max_tokens_to_sample"],
        do_stream=language_model_config["do_stream"],
    )

    all_logging = LoggingDatabaseConnection(logging_config["database"])

    cmpl_pipeline = BasicRAGPipeline(
        llm,
        generation_config,
        db=db,
        embedding_model=embedding_model,
        embeddings_provider=embeddings_provider,
        logging_database=all_logging,
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=text_splitter_config["chunk_size"],
        chunk_overlap=text_splitter_config["chunk_overlap"],
        length_function=len,
        is_separator_regex=False,
    )
    dataset_provider = HuggingFaceDataProvider()

    embd_pipeline = BasicEmbeddingPipeline(
        embedding_model,
        embeddings_provider,
        db,
        logging_database=all_logging,
        text_splitter=text_splitter,
    )

    app = create_app(
        embedding_pipeline=embd_pipeline,
        rag_pipeline=cmpl_pipeline,
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)
