import { cookies, headers } from "next/headers";

import { TransactionDetailShell } from "../../../../components/dashboard/transaction-detail-shell";
import { SiteFooter } from "../../../../components/layout/site-footer";
import { SiteHeader } from "../../../../components/layout/site-header";
import { ADMIN_SESSION_COOKIE_NAME } from "../../../../lib/auth-session";
import type { RouterTransactionDetail } from "../../../../lib/dashboard-api";

type PageParams = {
  reference: string;
};

type SearchParams = {
  created_at?: string | string[];
};

function pickCreatedAt(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }

  return value ?? null;
}

async function resolveTransactionDetail(
  reference: string,
  createdAt?: string | null,
) {
  const requestHeaders = await headers();
  const requestCookies = await cookies();
  const adminToken = requestCookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
  const protocol = requestHeaders.get("x-forwarded-proto") ?? "http";
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "127.0.0.1:3000";

  const detailUrl = new URL(
    `/api/admin/router/transactions/${encodeURIComponent(reference)}`,
    `${protocol}://${host}`,
  );

  if (createdAt) {
    detailUrl.searchParams.set("created_at", createdAt);
  }

  try {
    const response = await fetch(detailUrl.toString(), {
      cache: "no-store",
      headers: adminToken
        ? {
            Cookie: `${ADMIN_SESSION_COOKIE_NAME}=${adminToken}`,
          }
        : undefined,
    });
    const body = await response.json().catch(() => null);

    return { response, body };
  } catch {
    return { response: null, body: null };
  }
}

export default async function AdminTransactionDetailPage({
  params,
  searchParams,
}: {
  params: Promise<PageParams>;
  searchParams: Promise<SearchParams>;
}) {
  const { reference } = await params;
  const query = await searchParams;
  const createdAt = pickCreatedAt(query.created_at);
  const { response, body } = await resolveTransactionDetail(reference, createdAt);

  let state:
    | { kind: "success"; detail: RouterTransactionDetail }
    | { kind: "not-found"; message?: string }
    | { kind: "auth-required"; message?: string }
    | { kind: "forbidden"; message?: string }
    | { kind: "error"; message?: string };

  if (response?.ok && body) {
    state = { kind: "success", detail: body as RouterTransactionDetail };
  } else if (response?.status === 404) {
    state = {
      kind: "not-found",
      message: body?.detail ?? "We could not find a transaction for that reference.",
    };
  } else if (response?.status === 401) {
    state = {
      kind: "auth-required",
      message:
        body?.detail ?? "Your admin session is not authorized to view this transaction.",
    };
  } else if (response?.status === 403) {
    state = {
      kind: "forbidden",
      message:
        body?.detail ?? "Your account does not have permission to view this transaction.",
    };
  } else {
    state = {
      kind: "error",
      message:
        body?.detail ?? "Unable to load transaction detail from the admin proxy.",
    };
  }

  return (
    <div className="site-shell">
      <SiteHeader />
      <TransactionDetailShell
        createdAt={createdAt}
        reference={reference}
        state={state}
      />
      <SiteFooter />
    </div>
  );
}
