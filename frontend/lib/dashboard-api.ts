export type RouterGatewayHealth = {
  gateway_code: string;
  gateway_name: string;
  is_active: boolean;
  supports_collections: boolean;
  supports_payouts: boolean;
  priority_weight: number;
  success_rate_5m: number;
  success_rate_1h: number;
  timeout_rate_5m: number;
  p95_latency_ms: number;
  circuit_state: string;
  last_checked_at: string | null;
};

export type RouterTransaction = {
  reference: string;
  selected_gateway: string | null;
  status: string;
  amount: number;
  currency: string;
  created_at: string;
};

export type RouterTransactionDetail = {
  transaction: {
    reference: string;
    gateway_reference: string | null;
    type: string | null;
    selected_gateway: string | null;
    status: string;
    amount: number;
    currency: string;
    created_at: string;
    updated_at: string;
    merchant_name: string | null;
    customer_email: string | null;
  };
  routing_decision: {
    selected_gateway: string | null;
    reason: string | null;
    fallback_order: string[];
    eligible_gateways: string[];
    rejected_gateways: Record<string, unknown>;
    score_breakdown: Record<string, number>;
  };
  attempts: Array<{
    attempt_no: number;
    gateway: string;
    status: string;
    gateway_reference: string | null;
    latency_ms: number | null;
    error_code: string | null;
    error_message: string | null;
    created_at: string;
  }>;
  failover_summary: {
    did_failover: boolean;
    failover_count: number;
    recovered_after_failover: boolean;
  };
  webhook_trace: {
    last_event: string | null;
    last_status: string | null;
    last_gateway: string | null;
    is_reconciling: boolean;
  };
};

export type RouterFailover = {
  reference: string;
  selected_gateway: string | null;
  attempt_count: number;
  fallback_order: string[];
  created_at: string;
};

export type RouterDashboardData = {
  summary: {
    total_gateways: number;
    active_gateways: number;
    recent_failover_count: number;
    routed_transaction_count: number;
  };
  gateway_health: RouterGatewayHealth[];
  recent_transactions: RouterTransaction[];
  recent_failovers: RouterFailover[];
};

export type RouterGatewayControlPayload = {
  gateway_name: string;
  is_active?: boolean;
  priority_weight?: number;
  supports_collections: boolean;
  supports_payouts: boolean;
};

export type RouterGatewayControlResult = {
  gateway: {
    gateway_code: string;
    gateway_name: string;
    is_active: boolean;
    priority_weight: number;
    supports_collections: boolean;
    supports_payouts: boolean;
  };
};

export type RouterRule = {
  id: number;
  name: string;
  operation: string;
  channel: string | null;
  min_amount: number | null;
  max_amount: number | null;
  allow_gateways: string[];
  deny_gateways: string[];
  force_priority_order: string[];
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type RouterRuleCreatePayload = {
  name: string;
  operation: string;
  channel?: string | null;
  min_amount?: number | null;
  max_amount?: number | null;
  allow_gateways: string[];
  deny_gateways: string[];
  force_priority_order: string[];
  enabled?: boolean;
};

export type RouterRuleUpdatePayload = {
  name?: string;
  operation?: string;
  channel?: string | null;
  min_amount?: number | null;
  max_amount?: number | null;
  allow_gateways?: string[];
  deny_gateways?: string[];
  force_priority_order?: string[];
  enabled?: boolean;
};
