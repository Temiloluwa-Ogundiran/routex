import { PLAYGROUND_ENDPOINTS } from "./playground-endpoints";
import { getApiBaseUrl } from "./runtime-config";

export const PUBLIC_OPENAPI_URL = "/public/openapi.json";

type EndpointMethod = "GET" | "POST";

export type ApiReferenceEndpoint = {
  id: string;
  method: EndpointMethod;
  path: string;
  description: string;
};

export type ApiReferenceGroup = {
  title: string;
  description: string;
  endpoints: ApiReferenceEndpoint[];
};

export type ApiReferenceData = {
  groups: ApiReferenceGroup[];
  sourceLabel: string;
  sourceMode: "live" | "fallback";
};

type OpenApiPathOperation = {
  summary?: string;
  description?: string;
};

type OpenApiDocument = {
  paths?: Record<string, Partial<Record<string, OpenApiPathOperation>>>;
};

function buildFallbackGroups(): ApiReferenceGroup[] {
  return [
    {
      title: "Collections",
      description: "Accept customer payments through the routed collections surface.",
      endpoints: PLAYGROUND_ENDPOINTS.filter(
        (endpoint) => endpoint.id !== "payout",
      ).map((endpoint) => ({
        id: endpoint.id,
        method: endpoint.method,
        path: endpoint.path,
        description: endpoint.description,
      })),
    },
    {
      title: "Payouts",
      description: "Move funds out through the unified payout and wallet layer.",
      endpoints: PLAYGROUND_ENDPOINTS.filter(
        (endpoint) => endpoint.id === "payout",
      ).map((endpoint) => ({
        id: endpoint.id,
        method: endpoint.method,
        path: endpoint.path,
        description: endpoint.description,
      })),
    },
  ];
}

function createEmptyGroups(): Record<string, ApiReferenceGroup> {
  return {
    Collections: {
      title: "Collections",
      description: "Accept customer payments through the routed collections surface.",
      endpoints: [],
    },
    Payouts: {
      title: "Payouts",
      description: "Move funds out through the unified payout and wallet layer.",
      endpoints: [],
    },
    Operations: {
      title: "Operations",
      description: "Inspect public router utilities and operational helpers.",
      endpoints: [],
    },
  };
}

function normalizeOperationMethod(method: string): EndpointMethod | null {
  if (method === "get") {
    return "GET";
  }

  if (method === "post") {
    return "POST";
  }

  return null;
}

function classifyPath(path: string) {
  if (path.includes("payout")) {
    return "Payouts";
  }

  if (path.includes("initiate") || path.includes("verify")) {
    return "Collections";
  }

  return "Operations";
}

function buildGroupsFromOpenApi(document: OpenApiDocument): ApiReferenceGroup[] {
  const groups = createEmptyGroups();
  const paths = document.paths ?? {};

  for (const [path, operations] of Object.entries(paths)) {
    for (const [methodKey, operation] of Object.entries(operations ?? {})) {
      const method = normalizeOperationMethod(methodKey);
      if (!method) {
        continue;
      }

      const group = groups[classifyPath(path)];
      group.endpoints.push({
        id: `${methodKey}-${path}`,
        method,
        path,
        description:
          operation?.summary ??
          operation?.description ??
          "Public RouteX API endpoint.",
      });
    }
  }

  return Object.values(groups).filter((group) => group.endpoints.length > 0);
}

export async function getApiReferenceData(): Promise<ApiReferenceData> {
  const baseUrl = getApiBaseUrl();

  if (!baseUrl) {
    return {
      groups: buildFallbackGroups(),
      sourceLabel: PUBLIC_OPENAPI_URL,
      sourceMode: "fallback",
    };
  }

  try {
    const response = await fetch(`${baseUrl}${PUBLIC_OPENAPI_URL}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        groups: buildFallbackGroups(),
        sourceLabel: PUBLIC_OPENAPI_URL,
        sourceMode: "fallback",
      };
    }

    const document = (await response.json()) as OpenApiDocument;
    return {
      groups: buildGroupsFromOpenApi(document),
      sourceLabel: `${baseUrl}${PUBLIC_OPENAPI_URL}`,
      sourceMode: "live",
    };
  } catch {
    return {
      groups: buildFallbackGroups(),
      sourceLabel: PUBLIC_OPENAPI_URL,
      sourceMode: "fallback",
    };
  }
}
