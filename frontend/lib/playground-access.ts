import { cookies } from "next/headers";

import { USER_SESSION_COOKIE_NAME } from "./auth-session";
import { getApiBaseUrl, getPlaygroundSecretKey } from "./runtime-config";

type MerchantRecord = {
  id: string;
  name: string;
};

type UserProfileResponse = {
  merchants?: MerchantRecord[];
  detail?: string;
  message?: string;
};

type MerchantTokenResponse = {
  test?: {
    secret?: string | null;
  };
  detail?: string;
  message?: string;
};

export type PlaygroundAccess = {
  apiBaseUrl: string | null;
  available: boolean;
  message: string;
  secretKey: string | null;
  statusLabel: string;
};

async function parseJson<T>(response: Response): Promise<T | null> {
  return response.json().catch(() => null);
}

export async function resolvePlaygroundAccess(): Promise<PlaygroundAccess> {
  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return {
      apiBaseUrl: null,
      available: false,
      message: "Sandbox access is not configured on this deployment yet.",
      secretKey: null,
      statusLabel: "Setup required",
    };
  }

  const configuredSecretKey = getPlaygroundSecretKey();
  if (configuredSecretKey) {
    return {
      apiBaseUrl,
      available: true,
      message: "Sandbox requests are ready for this deployment.",
      secretKey: configuredSecretKey,
      statusLabel: "Configured sandbox",
    };
  }

  const requestCookies = await cookies();
  const userSessionToken = requestCookies.get(USER_SESSION_COOKIE_NAME)?.value;
  if (!userSessionToken) {
    return {
      apiBaseUrl,
      available: false,
      message: "Sign in with a merchant account to unlock the sandbox.",
      secretKey: null,
      statusLabel: "Sign in required",
    };
  }

  const userResponse = await fetch(`${apiBaseUrl}/get-user`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${userSessionToken}`,
    },
  });

  const userProfile = await parseJson<UserProfileResponse>(userResponse);
  const merchant = userProfile?.merchants?.[0];

  if (!userResponse.ok || !merchant) {
    return {
      apiBaseUrl,
      available: false,
      message:
        userProfile?.detail ??
        userProfile?.message ??
        "Create a merchant workspace to unlock the sandbox.",
      secretKey: null,
      statusLabel: "Workspace required",
    };
  }

  const tokenResponse = await fetch(`${apiBaseUrl}/get-token`, {
    body: JSON.stringify({ id: merchant.id }),
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${userSessionToken}`,
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  const tokenPayload = await parseJson<MerchantTokenResponse>(tokenResponse);
  const testSecretKey = tokenPayload?.test?.secret ?? null;

  if (!tokenResponse.ok || !testSecretKey) {
    return {
      apiBaseUrl,
      available: false,
      message:
        tokenPayload?.detail ??
        tokenPayload?.message ??
        "Your merchant workspace does not have a usable test key yet.",
      secretKey: null,
      statusLabel: "Key unavailable",
    };
  }

  return {
    apiBaseUrl,
    available: true,
    message: `Signed in with ${merchant.name} test workspace.`,
    secretKey: testSecretKey,
    statusLabel: "Merchant sandbox",
  };
}
