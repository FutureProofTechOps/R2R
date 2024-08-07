import logging
from typing import Optional, Any, Union
from pydantic import BaseModel 
from dataclasses import dataclass
from typing import Any
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Identified:
    """A protocol for an item with an ID."""

    id: str
    """The ID of the item."""

    short_id: str | None
    """Human readable ID used to refer to this community in prompts or texts displayed to users, such as in a report text (optional)."""

@dataclass
class Named(Identified):
    """A protocol for an item with a name/title."""

    title: str
    """The name/title of the item."""

class Triple(BaseModel):
    """A relationship between two entities. This is a generic relationship, and can be used to represent any type of relationship between any two entities."""

    id: str
    
    subject: str
    """The source entity name."""

    object: str
    """The target entity name."""

    weight: float | None = 1.0
    """The edge weight."""

    description: str | None = None
    """A description of the relationship (optional)."""

    predicate: str | None = None
    """A description of the relationship (optional)."""

    predicate_embedding: list[float] | None = None
    """The semantic embedding for the relationship description (optional)."""

    text_unit_ids: list[str] | None = None
    """List of text unit IDs in which the relationship appears (optional)."""

    document_ids: list[str] | None = None
    """List of document IDs in which the relationship appears (optional)."""

    attributes: dict[str, Any] | None = None
    """Additional attributes associated with the relationship (optional). To be included in the search prompt"""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        source_key: str = "subject",
        target_key: str = "object",
        predicate_key: str = "predicate",
        description_key: str = "description",
        weight_key: str = "weight",
        text_unit_ids_key: str = "text_unit_ids",
        document_ids_key: str = "document_ids",
        attributes_key: str = "attributes",
    ) -> "Relationship":
        """Create a new relationship from the dict data."""
        return Triple(
            id=d[id_key],
            short_id=d.get(short_id_key),
            subject=d[source_key],
            object=d[target_key],
            predicate=d.get(predicate_key),
            description=d.get(description_key),
            weight=d.get(weight_key, 1.0),
            text_unit_ids=d.get(text_unit_ids_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )

class Entity(BaseModel):
    """An entity extracted from a document."""

    id: str
    category: str
    subcategory: Optional[str] = None
    value: str
    description: Optional[str] = None
    description_embedding: list[float] = None
    name_embedding: list[float] = None
    graph_embedding: list[float] = None
    community_ids: list[str] = None
    text_unit_ids: list[str] = None
    document_ids: list[str] = None
    rank: int | None = 1
    attributes: dict[str, Any] = None

    def __str__(self):
        return (
            f"{self.category}:{self.subcategory}:{self.value}"
            if self.subcategory
            else f"{self.category}:{self.value}"
        )


@dataclass
class Community(Named):
    """A protocol for a community in the system."""

    level: str = ""
    """Community level."""

    entity_ids: list[str] | None = None
    """List of entity IDs related to the community (optional)."""

    relationship_ids: list[str] | None = None
    """List of relationship IDs related to the community (optional)."""

    covariate_ids: dict[str, list[str]] | None = None
    """Dictionary of different types of covariates related to the community (optional), e.g. claims"""

    attributes: dict[str, Any] | None = None
    """A dictionary of additional attributes associated with the community (optional). To be included in the search prompt."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        title_key: str = "title",
        short_id_key: str = "short_id",
        level_key: str = "level",
        entities_key: str = "entity_ids",
        relationships_key: str = "relationship_ids",
        covariates_key: str = "covariate_ids",
        attributes_key: str = "attributes",
    ) -> "Community":
        """Create a new community from the dict data."""
        return Community(
            id=d[id_key],
            title=d[title_key],
            short_id=d.get(short_id_key),
            level=d[level_key],
            entity_ids=d.get(entities_key),
            relationship_ids=d.get(relationships_key),
            covariate_ids=d.get(covariates_key),
            attributes=d.get(attributes_key),
        )

@dataclass
class CommunityReport(Named):
    """Defines an LLM-generated summary report of a community."""

    community_id: str
    """The ID of the community this report is associated with."""

    summary: str = ""
    """Summary of the report."""

    full_content: str = ""
    """Full content of the report."""

    rank: float | None = 1.0
    """Rank of the report, used for sorting (optional). Higher means more important"""

    summary_embedding: list[float] | None = None
    """The semantic (i.e. text) embedding of the report summary (optional)."""

    full_content_embedding: list[float] | None = None
    """The semantic (i.e. text) embedding of the full report content (optional)."""

    attributes: dict[str, Any] | None = None
    """A dictionary of additional attributes associated with the report (optional)."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        title_key: str = "title",
        community_id_key: str = "community_id",
        short_id_key: str = "short_id",
        summary_key: str = "summary",
        full_content_key: str = "full_content",
        rank_key: str = "rank",
        summary_embedding_key: str = "summary_embedding",
        full_content_embedding_key: str = "full_content_embedding",
        attributes_key: str = "attributes",
    ) -> "CommunityReport":
        """Create a new community report from the dict data."""
        return CommunityReport(
            id=d[id_key],
            title=d[title_key],
            community_id=d[community_id_key],
            short_id=d.get(short_id_key),
            summary=d[summary_key],
            full_content=d[full_content_key],
            rank=d[rank_key],
            summary_embedding=d.get(summary_embedding_key),
            full_content_embedding=d.get(full_content_embedding_key),
            attributes=d.get(attributes_key),
        )

@dataclass
class Covariate(Identified):
    """
    A protocol for a covariate in the system.

    Covariates are metadata associated with a subject, e.g. entity claims.
    Each subject (e.g. entity) may be associated with multiple types of covariates.
    """

    subject_id: str
    """The subject id."""

    subject_type: str = "entity"
    """The subject type."""

    covariate_type: str = "claim"
    """The covariate type."""

    text_unit_ids: list[str] | None = None
    """List of text unit IDs in which the covariate info appears (optional)."""

    document_ids: list[str] | None = None
    """List of document IDs in which the covariate info appears (optional)."""

    attributes: dict[str, Any] | None = None

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        subject_id_key: str = "subject_id",
        subject_type_key: str = "subject_type",
        covariate_type_key: str = "covariate_type",
        short_id_key: str = "short_id",
        text_unit_ids_key: str = "text_unit_ids",
        document_ids_key: str = "document_ids",
        attributes_key: str = "attributes",
    ) -> "Covariate":
        """Create a new covariate from the dict data."""
        return Covariate(
            id=d[id_key],
            short_id=d.get(short_id_key),
            subject_id=d[subject_id_key],
            subject_type=d.get(subject_type_key, "entity"),
            covariate_type=d.get(covariate_type_key, "claim"),
            text_unit_ids=d.get(text_unit_ids_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )
    

@dataclass
class TextUnit(Identified):
    """A protocol for a TextUnit item in a Document database."""

    text: str
    """The text of the unit."""

    text_embedding: list[float] | None = None
    """The text embedding for the text unit (optional)."""

    entity_ids: list[str] | None = None
    """List of entity IDs related to the text unit (optional)."""

    relationship_ids: list[str] | None = None
    """List of relationship IDs related to the text unit (optional)."""

    covariate_ids: dict[str, list[str]] | None = None
    "Dictionary of different types of covariates related to the text unit (optional)."

    n_tokens: int | None = None
    """The number of tokens in the text (optional)."""

    document_ids: list[str] | None = None
    """List of document IDs in which the text unit appears (optional)."""

    attributes: dict[str, Any] | None = None
    """A dictionary of additional attributes associated with the text unit (optional)."""

    @classmethod
    def from_dict(
        cls,
        d: dict[str, Any],
        id_key: str = "id",
        short_id_key: str = "short_id",
        text_key: str = "text",
        text_embedding_key: str = "text_embedding",
        entities_key: str = "entity_ids",
        relationships_key: str = "relationship_ids",
        covariates_key: str = "covariate_ids",
        n_tokens_key: str = "n_tokens",
        document_ids_key: str = "document_ids",
        attributes_key: str = "attributes",
    ) -> "TextUnit":
        """Create a new text unit from the dict data."""
        return TextUnit(
            id=d[id_key],
            short_id=d.get(short_id_key),
            text=d[text_key],
            text_embedding=d.get(text_embedding_key),
            entity_ids=d.get(entities_key),
            relationship_ids=d.get(relationships_key),
            covariate_ids=d.get(covariates_key),
            n_tokens=d.get(n_tokens_key),
            document_ids=d.get(document_ids_key),
            attributes=d.get(attributes_key),
        )

from collections.abc import Callable

TextEmbedder = Callable[[str], list[float]]

def extract_entities(llm_payload: list[str]) -> dict[str, Entity]:
    entities = {}
    for entry in llm_payload:
        try:
            if "], " in entry:  # Check if the entry is an entity
                entry_val = entry.split("], ")[0] + "]"
                entry = entry.split("], ")[1]
                colon_count = entry.count(":")

                if colon_count == 1:
                    category, value = entry.split(":")
                    subcategory = None
                elif colon_count >= 2:
                    parts = entry.split(":", 2)
                    category, subcategory, value = (
                        parts[0],
                        parts[1],
                        parts[2],
                    )
                else:
                    raise ValueError("Unexpected entry format")

                entities[entry_val] = Entity(
                    category=category, subcategory=subcategory, value=value
                )
        except Exception as e:
            logger.error(f"Error processing entity {entry}: {e}")
            continue
    return entities


def extract_triples(
    llm_payload: list[str], entities: dict[str, Entity]
) -> list[Triple]:
    triples = []
    for entry in llm_payload:
        try:
            if "], " not in entry:  # Check if the entry is an entity
                elements = entry.split(" ")
                subject = elements[0]
                predicate = elements[1]
                object = " ".join(elements[2:])
                subject = entities[subject].value  # Use entity.value
                if "[" in object and "]" in object:
                    object = entities[object].value  # Use entity.value
                triples.append(
                    Triple(subject=subject, predicate=predicate, object=object)
                )
        except Exception as e:
            logger.error(f"Error processing triplet {entry}: {e}")
            continue
    return triples

class KGExtraction(BaseModel):
    """An extraction from a document that is part of a knowledge graph."""

    entities: Union[list[Entity], dict[str, Entity]]
    triples: list[Triple]