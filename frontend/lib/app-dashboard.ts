export type MerchantWorkspaceUser = {
  id: string;
  name: string;
  email: string;
  is_verified: boolean;
};

export type MerchantWorkspaceMerchant = {
  id: string;
  name: string;
  email: string;
  is_verified: boolean;
  is_active: boolean;
  joined_at: string;
  test_balance: number;
  live_balance: number;
  percentage_charge: number;
  flat_charge: number;
  role?: string | null;
};

export type MerchantWorkspaceSummary = {
  mode: string;
  period: string;
  revenue_metrics: {
    total_revenue: number;
    total_transactions: number;
    total_charges: number;
    net_revenue: number;
    average_transaction_value: number;
    success_rate: number;
  };
  transaction_breakdown: {
    successful: number;
    pending: number;
    failed: number;
    total: number;
  };
  top_currency: {
    currency: string;
    total_revenue: number;
    transaction_count: number;
    total_charges: number;
    net_revenue: number;
    average_transaction_value: number;
  } | null;
  wallet_count: number;
  total_balance: number;
  pending_payouts: number;
  pending_payout_amount: number;
};

export type MerchantWorkspaceWallet = {
  id: number;
  merchant_id: string;
  currency: string;
  balance: number;
  mode: string;
  percentage_charge: number;
  flat_charge: number;
  payout_percentage_charge: number;
  payout_flat_charge: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type MerchantWorkspaceTransaction = {
  id: number;
  type: string | null;
  mode: string | null;
  reference: string;
  status: string;
  currency: string;
  amount: number;
  charge: number;
  processor_reference: string | null;
  customer: {
    name?: string | null;
    email?: string | null;
  } | null;
  details: Record<string, unknown> | null;
  created_at: string;
};

export type MerchantWorkspaceTransactionsPage = {
  transactions: MerchantWorkspaceTransaction[];
  total_items: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  filters: {
    wallet_id: number | null;
    currency: string | null;
    transaction_type: string | null;
  };
};

export type MerchantWorkspacePaymentLink = {
  id: string;
  reference: string;
  title: string;
  merchant_id: string;
  url: string;
  description: string | null;
  amount_type: string;
  mode: string;
  type: string;
  currency: string;
  gateway_code?: string | null;
  amount: number | null;
  max_uses: number | null;
  current_uses: number;
  redirect_url: string | null;
  expires_at: string | null;
  _metadata: string | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
};

export type MerchantWorkspaceTokens = {
  merchant_id: string;
  live: {
    secret: string | null;
    public: string | null;
  };
  test: {
    secret: string | null;
    public: string | null;
  };
};

export type MerchantDashboardData = {
  user: MerchantWorkspaceUser;
  merchants: MerchantWorkspaceMerchant[];
  selected_merchant: MerchantWorkspaceMerchant | null;
  mode: "test" | "live";
  period: string;
  summary: MerchantWorkspaceSummary | null;
  wallets: MerchantWorkspaceWallet[];
  transactions: MerchantWorkspaceTransactionsPage;
  payment_links: MerchantWorkspacePaymentLink[];
  api_tokens: MerchantWorkspaceTokens | null;
  warnings: string[];
};

export type MerchantDashboardResponse = {
  status: boolean;
  message?: string;
  data?: MerchantDashboardData;
};

export function normalizeMode(value: string | null | undefined): "test" | "live" {
  return value === "live" ? "live" : "test";
}

export function maskApiKey(value: string | null | undefined) {
  if (!value) {
    return "Not available yet";
  }

  if (value.length <= 16) {
    return value;
  }

  return `${value.slice(0, 12)}...${value.slice(-6)}`;
}
