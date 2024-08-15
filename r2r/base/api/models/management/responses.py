from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from r2r.base.api.models.base import ResultsWrapper


class PromptResponse(BaseModel):
    message: str


class LogEntry(BaseModel):
    key: str
    value: Any
    timestamp: datetime


class LogResponse(BaseModel):
    run_id: UUID
    run_type: str
    entries: List[LogEntry]
    timestamp: Optional[datetime]
    user_id: Optional[UUID]


class ServerStats(BaseModel):
    start_time: datetime
    uptime_seconds: float
    cpu_usage: float
    memory_usage: float


class AnalyticsResponse(BaseModel):
    analytics_data: Any
    filtered_logs: Dict[str, Any]


class AppSettingsResponse(BaseModel):
    config: Dict[str, Any]
    prompts: Dict[str, Any]


class ScoreCompletionResponse(BaseModel):
    message: str


class UserOverviewResponse(BaseModel):
    user_id: UUID
    num_files: int
    total_size_in_bytes: int
    document_ids: List[UUID]


class DeleteResponse(BaseModel):
    fragment_id: UUID
    document_id: UUID
    extraction_id: UUID
    text: str


class DocumentOverviewResponse(BaseModel):
    id: UUID
    title: str
    user_id: UUID
    type: str
    created_at: datetime
    updated_at: datetime
    status: str
    version: str


class DocumentChunkResponse(BaseModel):
    fragment_id: UUID
    extraction_id: UUID
    document_id: UUID
    user_id: UUID
    group_ids: list[UUID]
    text: str
    metadata: Dict[str, Any]


KnowledgeGraphResponse = str


class GroupResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class GroupOverviewResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    user_count: int
    document_count: int


# Create wrapped versions of each response
WrappedPromptResponse = ResultsWrapper[PromptResponse]
WrappedServerStatsResponse = ResultsWrapper[ServerStats]
WrappedLogResponse = ResultsWrapper[List[LogResponse]]
WrappedAnalyticsResponse = ResultsWrapper[AnalyticsResponse]
WrappedAppSettingsResponse = ResultsWrapper[AppSettingsResponse]
WrappedScoreCompletionResponse = ResultsWrapper[ScoreCompletionResponse]
WrappedUserOverviewResponse = ResultsWrapper[List[UserOverviewResponse]]
WrappedDeleteResponse = ResultsWrapper[dict[str, DeleteResponse]]
WrappedDocumentOverviewResponse = ResultsWrapper[
    List[DocumentOverviewResponse]
]
WrappedDocumentChunkResponse = ResultsWrapper[List[DocumentChunkResponse]]
WrappedKnowledgeGraphResponse = ResultsWrapper[KnowledgeGraphResponse]
WrappedGroupResponse = ResultsWrapper[GroupResponse]
WrappedGroupListResponse = ResultsWrapper[List[GroupResponse]]
WrappedGroupOverviewResponse = ResultsWrapper[List[GroupOverviewResponse]]
