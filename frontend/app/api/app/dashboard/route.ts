import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { USER_SESSION_COOKIE_NAME } from "../../../../lib/auth-session";
import {
  normalizeMode,
  type MerchantDashboardData,
  type MerchantWorkspaceMerchant,
  type MerchantWorkspacePaymentLink,
  type MerchantWorkspaceSummary,
  type MerchantWorkspaceTokens,
  type MerchantWorkspaceTransactionsPage,
  type MerchantWorkspaceUser,
  type MerchantWorkspaceWallet,
} from "../../../../lib/app-dashboard";
import { getApiBaseUrl } from "../../../../lib/runtime-config";

type BackendResponse<T> = {
  ok: boolean;
  status: number;
  data: T | null;
};

async function parseBackendResponse<T>(
  response: Response,
): Promise<BackendResponse<T>> {
  const data = (await response.json().catch(() => null)) as T | null;
  return {
    ok: response.ok,
    status: response.status,
    data,
  };
}

async function fetchBackendJson<T>(
  apiBaseUrl: string,
  userToken: string,
  path: string,
  init?: RequestInit,
) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${userToken}`,
      ...(init?.headers ?? {}),
    },
  });

  return parseBackendResponse<T>(response);
}

function buildEmptyTransactionsPage(): MerchantWorkspaceTransactionsPage {
  return {
    transactions: [],
    total_items: 0,
    total_pages: 0,
    current_page: 1,
    page_size: 6,
    filters: {
      wallet_id: null,
      currency: null,
      transaction_type: null,
    },
  };
}

function buildDashboardPayload(params: {
  user: MerchantWorkspaceUser;
  merchants: MerchantWorkspaceMerchant[];
  selectedMerchant: MerchantWorkspaceMerchant | null;
  mode: "test" | "live";
  period: string;
  summary: MerchantWorkspaceSummary | null;
  wallets: MerchantWorkspaceWallet[];
  transactions: MerchantWorkspaceTransactionsPage;
  paymentLinks: MerchantWorkspacePaymentLink[];
  apiTokens: MerchantWorkspaceTokens | null;
  warnings: string[];
}): MerchantDashboardData {
  return {
    user: params.user,
    merchants: params.merchants,
    selected_merchant: params.selectedMerchant,
    mode: params.mode,
    period: params.period,
    summary: params.summary,
    wallets: params.wallets,
    transactions: params.transactions,
    payment_links: params.paymentLinks,
    api_tokens: params.apiTokens,
    warnings: params.warnings,
  };
}

export async function GET(request: NextRequest) {
  const requestCookies = await cookies();
  const userToken = requestCookies.get(USER_SESSION_COOKIE_NAME)?.value;
  if (!userToken) {
    return NextResponse.json(
      { status: false, message: "Not authenticated" },
      { status: 401 },
    );
  }

  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { status: false, message: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  const url = new URL(request.url);
  const requestedMerchantId = url.searchParams.get("merchantId");
  const mode = normalizeMode(url.searchParams.get("mode"));
  const period = url.searchParams.get("period")?.trim() || "month";

  const userResponse = await fetchBackendJson<{
    id: string;
    name: string;
    email: string;
    is_verified: boolean;
    merchants?: MerchantWorkspaceMerchant[];
  }>(apiBaseUrl, userToken, "/get-user");

  if (!userResponse.ok || !userResponse.data) {
    return NextResponse.json(
      {
        status: false,
        message: "We could not load your user profile.",
      },
      { status: userResponse.status || 502 },
    );
  }

  const user: MerchantWorkspaceUser = {
    id: userResponse.data.id,
    name: userResponse.data.name,
    email: userResponse.data.email,
    is_verified: userResponse.data.is_verified,
  };

  const merchants = Array.isArray(userResponse.data.merchants)
    ? userResponse.data.merchants
    : [];
  const selectedMerchant =
    merchants.find((merchant) => merchant.id === requestedMerchantId) ??
    merchants[0] ??
    null;

  if (!selectedMerchant) {
    return NextResponse.json({
      status: true,
      data: buildDashboardPayload({
        user,
        merchants,
        selectedMerchant: null,
        mode,
        period,
        summary: null,
        wallets: [],
        transactions: buildEmptyTransactionsPage(),
        paymentLinks: [],
        apiTokens: null,
        warnings: [],
      }),
    });
  }

  const warnings: string[] = [];
  const [summaryResponse, walletsResponse, transactionsResponse, linksResponse, tokensResponse] =
    await Promise.all([
      fetchBackendJson<MerchantWorkspaceSummary>(
        apiBaseUrl,
        userToken,
        `/analytics/dashboard?merchant_id=${encodeURIComponent(selectedMerchant.id)}&mode=${mode}&period=${encodeURIComponent(period)}`,
      ),
      fetchBackendJson<MerchantWorkspaceWallet[]>(
        apiBaseUrl,
        userToken,
        `/wallets?merchant_id=${encodeURIComponent(selectedMerchant.id)}&mode=${mode}`,
      ),
      fetchBackendJson<MerchantWorkspaceTransactionsPage>(
        apiBaseUrl,
        userToken,
        `/merchant-transactions?merchant_id=${encodeURIComponent(selectedMerchant.id)}&mode=${mode}&page_size=6`,
      ),
      fetchBackendJson<MerchantWorkspacePaymentLink[]>(
        apiBaseUrl,
        userToken,
        `/links/merchant/${encodeURIComponent(selectedMerchant.id)}`,
      ),
      fetchBackendJson<MerchantWorkspaceTokens & { merchant_id?: string }>(
        apiBaseUrl,
        userToken,
        "/get-token",
        {
          body: JSON.stringify({ id: selectedMerchant.id }),
          headers: {
            "Content-Type": "application/json",
          },
          method: "POST",
        },
      ),
    ]);

  if (!summaryResponse.ok) {
    warnings.push("Dashboard analytics are temporarily unavailable.");
  }
  if (!walletsResponse.ok) {
    warnings.push("Wallet balances could not be loaded.");
  }
  if (!transactionsResponse.ok) {
    warnings.push("Recent transactions could not be loaded.");
  }
  if (!linksResponse.ok) {
    warnings.push("Payment links could not be loaded.");
  }
  if (!tokensResponse.ok) {
    warnings.push("API keys could not be loaded.");
  }

  const dashboardData = buildDashboardPayload({
    user,
    merchants,
    selectedMerchant,
    mode,
    period,
    summary: summaryResponse.data,
    wallets: walletsResponse.data ?? [],
    transactions: transactionsResponse.data ?? buildEmptyTransactionsPage(),
    paymentLinks: linksResponse.data ?? [],
    apiTokens: tokensResponse.data
      ? {
          merchant_id: tokensResponse.data.merchant_id ?? selectedMerchant.id,
          live: {
            secret: tokensResponse.data.live?.secret ?? null,
            public: tokensResponse.data.live?.public ?? null,
          },
          test: {
            secret: tokensResponse.data.test?.secret ?? null,
            public: tokensResponse.data.test?.public ?? null,
          },
        }
      : null,
    warnings,
  });

  return NextResponse.json({
    status: true,
    data: dashboardData,
  });
}
