import logging
import uuid
from typing import Any, Optional

from fastapi import HTTPException

from r2r.core import (
    AnalysisTypes,
    FilterCriteria,
    KVLoggingSingleton,
    LogProcessor,
    RunManager,
)
from r2r.telemetry.telemetry_decorator import telemetry_event

from ..abstractions import (
    R2RDeleteRequest,
    R2RDocumentChunksRequest,
    R2RPipelines,
    R2RProviders,
    R2RUpdatePromptRequest,
    R2RUsersStatsRequest,
)
from ..assembly.config import R2RConfig
from .base import Service

logger = logging.getLogger(__name__)


class IngestionService(Service):
    def __init__(
        self,
        config: R2RConfig,
        providers: R2RProviders,
        pipelines: R2RPipelines,
        run_manager: RunManager,
        logging_connection: KVLoggingSingleton,
    ):
        super().__init__(
            config, providers, pipelines, run_manager, logging_connection
        )

    @telemetry_event("UpdatePrompt")
    async def update_prompt(self, request: R2RUpdatePromptRequest):
        self.providers.prompt.update_prompt(
            request.name, request.template, request.input_types
        )
        return {"results": f"Prompt '{request.name}' added successfully."}

    @telemetry_event("Logs")
    async def alogs(
        self,
        log_type_filter: Optional[str] = None,
        max_runs_requested: int = 100,
        *args: Any,
        **kwargs: Any,
    ):
        if self.logging_connection is None:
            raise HTTPException(
                status_code=404, detail="Logging provider not found."
            )
        if (
            self.config.app.get("max_logs_per_request", 100)
            > max_runs_requested
        ):
            raise HTTPException(
                status_code=400,
                detail="Max runs requested exceeds the limit.",
            )

        run_info = await self.logging_connection.get_run_info(
            limit=max_runs_requested,
            log_type_filter=log_type_filter,
        )
        run_ids = [run.run_id for run in run_info]
        if len(run_ids) == 0:
            return {"results": []}
        logs = await self.logging_connection.get_logs(run_ids)
        # Aggregate logs by run_id and include run_type
        aggregated_logs = []

        for run in run_info:
            run_logs = [log for log in logs if log["log_id"] == run.run_id]
            entries = [
                {"key": log["key"], "value": log["value"]} for log in run_logs
            ][
                ::-1
            ]  # Reverse order so that earliest logged values appear first.
            aggregated_logs.append(
                {
                    "run_id": run.run_id,
                    "run_type": run.log_type,
                    "entries": entries,
                }
            )

        return {"results": aggregated_logs}

    @telemetry_event("Analytics")
    async def aanalytics(
        self,
        filter_criteria: FilterCriteria,
        analysis_types: AnalysisTypes,
    ):
        run_info = await self.logging_connection.get_run_info(limit=100)
        run_ids = [info.run_id for info in run_info]

        if not run_ids:
            return {
                "results": {
                    "analytics_data": "No logs found.",
                    "filtered_logs": {},
                }
            }

        logs = await self.logging_connection.get_logs(run_ids=run_ids)

        filters = {}
        if filter_criteria.filters:
            for key, value in filter_criteria.filters.items():
                filters[key] = lambda log, value=value: (
                    any(
                        entry.get("key") == value
                        for entry in log.get("entries", [])
                    )
                    if "entries" in log
                    else log.get("key") == value
                )

        log_processor = LogProcessor(filters)
        for log in logs:
            if "entries" in log and isinstance(log["entries"], list):
                log_processor.process_log(log)
            elif "key" in log:
                log_processor.process_log(log)
            else:
                logger.warning(
                    f"Skipping log due to missing or malformed 'entries': {log}"
                )

        filtered_logs = dict(log_processor.populations.items())
        results = {"filtered_logs": filtered_logs}

        if analysis_types and analysis_types.analysis_types:
            for (
                filter_key,
                analysis_config,
            ) in analysis_types.analysis_types.items():
                if filter_key in filtered_logs:
                    analysis_type = analysis_config[0]
                    if analysis_type == "bar_chart":
                        extract_key = analysis_config[1]
                        results[filter_key] = (
                            AnalysisTypes.generate_bar_chart_data(
                                filtered_logs[filter_key], extract_key
                            )
                        )
                    elif analysis_type == "basic_statistics":
                        extract_key = analysis_config[1]
                        results[filter_key] = (
                            AnalysisTypes.calculate_basic_statistics(
                                filtered_logs[filter_key], extract_key
                            )
                        )
                    elif analysis_type == "percentile":
                        extract_key = analysis_config[1]
                        percentile = int(analysis_config[2])
                        results[filter_key] = (
                            AnalysisTypes.calculate_percentile(
                                filtered_logs[filter_key],
                                extract_key,
                                percentile,
                            )
                        )
                    else:
                        logger.warning(
                            f"Unknown analysis type for filter key '{filter_key}': {analysis_type}"
                        )

        return {"results": results}

    @telemetry_event("AppSettings")
    async def aapp_settings(self, *args: Any, **kwargs: Any):
        # config_data = self.config.app  # Assuming this holds your config.json data
        prompts = self.providers.prompt.get_all_prompts()
        return {
            "results": {
                "config": self.config.to_json(),
                "prompts": {
                    name: prompt.dict() for name, prompt in prompts.items()
                },
            }
        }

    @telemetry_event("UsersStats")
    async def ausers_stats(self, user_ids: Optional[list[uuid.UUID]] = None):
        return self.providers.vector_db.get_users_stats(
            [str(ele) for ele in user_ids]
        )

    @telemetry_event("Delete")
    async def delete(self, request: R2RDeleteRequest):
        ids = self.providers.vector_db.delete_by_metadata(
            request.keys, request.values
        )
        if not ids:
            raise HTTPException(
                status_code=404, detail="No entries found for deletion."
            )
        self.providers.vector_db.delete_documents_info(ids)
        return {"results": "Entries deleted successfully."}

    @telemetry_event("DocumentsInfo")
    async def adocuments_info(
        self,
        document_ids: Optional[list[uuid.UUID]] = None,
        user_ids: Optional[list[uuid.UUID]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        return self.providers.vector_db.get_documents_info(
            filter_document_ids=(
                [str(ele) for ele in document_ids] if document_ids else None
            ),
            filter_user_ids=(
                [str(ele) for ele in user_ids] if user_ids else None
            ),
        )

    @telemetry_event("DocumentChunks")
    async def document_chunks(self, request: R2RDocumentChunksRequest):
        return self.providers.vector_db.get_document_chunks(
            request.document_id
        )

    @telemetry_event("UsersStats")
    async def users_stats(self, request: R2RUsersStatsRequest):
        return self.providers.vector_db.get_users_stats(
            [str(ele) for ele in request.user_ids]
        )

    @telemetry_event("AppSettings")
    async def app_settings(self):
        prompts = self.providers.prompt.get_all_prompts()
        return {
            "results": {
                "config": self.config.to_json(),
                "prompts": {
                    name: prompt.dict() for name, prompt in prompts.items()
                },
            }
        }

    @telemetry_event("OpenAPISpec")
    def openapi_spec(self):
        from fastapi.openapi.utils import get_openapi

        return {
            "results": get_openapi(
                title="R2R Application API",
                version="1.0.0",
                routes=self.app.routes,
            )
        }
