from typing import Optional

from pydantic import BaseModel, Field


class RoutingMetadata(BaseModel):
    decision_id: Optional[str] = Field(
        default=None,
        description="Audit identifier for the routing decision.",
    )
    selection_reason: str = Field(
        default="highest score among eligible gateways",
        description="Human-readable summary of why the gateway was selected.",
    )
    fallback_order: list[str] = Field(
        default_factory=list,
        description="Ordered list of fallback gateways considered for the request.",
    )
    score_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Score per eligible gateway at decision time.",
    )


class RoutingAttemptSummary(BaseModel):
    attempt_no: int = Field(..., description="Attempt sequence number for the routed transaction.")
    gateway: str = Field(..., description="Gateway code used for the attempt.")
    status: str = Field(..., description="Normalized attempt status.")
    gateway_reference: Optional[str] = Field(
        default=None,
        description="Gateway-facing reference generated for the attempt.",
    )
    latency_ms: Optional[int] = Field(
        default=None,
        description="Observed attempt latency in milliseconds when available.",
    )
