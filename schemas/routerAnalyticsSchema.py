from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class RouterGatewayHealthItem(BaseModel):
    gateway_code: str
    gateway_name: str
    is_active: bool
    supports_collections: bool
    supports_payouts: bool
    priority_weight: float
    success_rate_5m: float
    success_rate_1h: float
    timeout_rate_5m: float
    p95_latency_ms: float
    circuit_state: str
    last_checked_at: Optional[datetime] = None


class RouterTransactionItem(BaseModel):
    reference: str
    selected_gateway: Optional[str]
    status: str
    amount: float
    currency: str
    created_at: datetime


class RouterFailoverItem(BaseModel):
    reference: str
    selected_gateway: Optional[str]
    attempt_count: int
    fallback_order: list[str] = Field(default_factory=list)
    created_at: datetime


class RouterDashboardSummary(BaseModel):
    total_gateways: int
    active_gateways: int
    recent_failover_count: int
    routed_transaction_count: int


class RouterDashboardResponse(BaseModel):
    summary: RouterDashboardSummary
    gateway_health: list[RouterGatewayHealthItem]
    recent_transactions: list[RouterTransactionItem]
    recent_failovers: list[RouterFailoverItem]


class RouterGatewayUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    priority_weight: Optional[float] = None


class RouterGatewayUpdateResponse(BaseModel):
    gateway_code: str
    gateway_name: str
    is_active: bool
    priority_weight: float
    supports_collections: bool
    supports_payouts: bool


class RouterRuleItem(BaseModel):
    id: int
    name: str
    operation: str
    channel: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    allow_gateways: list[str] = Field(default_factory=list)
    deny_gateways: list[str] = Field(default_factory=list)
    force_priority_order: list[str] = Field(default_factory=list)
    enabled: bool
    created_at: datetime
    updated_at: datetime


class RouterRuleCreateRequest(BaseModel):
    name: str
    operation: str
    channel: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    allow_gateways: list[str] = Field(default_factory=list)
    deny_gateways: list[str] = Field(default_factory=list)
    force_priority_order: list[str] = Field(default_factory=list)
    enabled: bool = True


class RouterRuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    operation: Optional[str] = None
    channel: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    allow_gateways: Optional[list[str]] = None
    deny_gateways: Optional[list[str]] = None
    force_priority_order: Optional[list[str]] = None
    enabled: Optional[bool] = None


class RouterTransactionDetailSummary(BaseModel):
    reference: str
    gateway_reference: Optional[str] = None
    type: Optional[str] = None
    selected_gateway: Optional[str]
    status: str
    amount: float
    currency: str
    created_at: datetime
    updated_at: datetime
    merchant_name: Optional[str] = None
    customer_email: Optional[str] = None


class RouterRoutingDecisionDetail(BaseModel):
    selected_gateway: Optional[str]
    reason: Optional[str] = None
    fallback_order: list[str] = Field(default_factory=list)
    eligible_gateways: list[str] = Field(default_factory=list)
    rejected_gateways: dict[str, Any] = Field(default_factory=dict)
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class RouterRoutingAttemptDetail(BaseModel):
    attempt_no: int
    gateway: str
    status: str
    gateway_reference: Optional[str] = None
    latency_ms: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


class RouterFailoverSummary(BaseModel):
    did_failover: bool
    failover_count: int
    recovered_after_failover: bool


class RouterWebhookTrace(BaseModel):
    last_event: Optional[str] = None
    last_status: Optional[str] = None
    last_gateway: Optional[str] = None
    is_reconciling: bool = False


class RouterTransactionDetailResponse(BaseModel):
    transaction: RouterTransactionDetailSummary
    routing_decision: RouterRoutingDecisionDetail
    attempts: list[RouterRoutingAttemptDetail]
    failover_summary: RouterFailoverSummary
    webhook_trace: RouterWebhookTrace
