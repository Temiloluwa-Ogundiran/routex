import { getApiBaseUrl } from "./runtime-config";

export const PUBLIC_OPENAPI_URL = "/public/openapi.json";

type EndpointMethod = "GET" | "POST";
type SourceMode = "live" | "unavailable";

type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue };

type OpenApiSchema = {
  $ref?: string;
  type?: string;
  title?: string;
  description?: string;
  format?: string;
  example?: unknown;
  default?: unknown;
  enum?: unknown[];
  properties?: Record<string, OpenApiSchema>;
  required?: string[];
  items?: OpenApiSchema;
  anyOf?: OpenApiSchema[];
  additionalProperties?: boolean | OpenApiSchema;
};

type OpenApiExample = {
  summary?: string;
  value?: unknown;
};

type OpenApiMediaType = {
  schema?: OpenApiSchema;
  example?: unknown;
  examples?: Record<string, OpenApiExample>;
};

type OpenApiParameter = {
  name: string;
  in: string;
  required?: boolean;
  description?: string;
  example?: unknown;
  schema?: OpenApiSchema;
};

type OpenApiResponse = {
  description?: string;
  content?: Record<string, OpenApiMediaType>;
};

type OpenApiOperation = {
  summary?: string;
  description?: string;
  parameters?: OpenApiParameter[];
  requestBody?: {
    required?: boolean;
    content?: Record<string, OpenApiMediaType>;
  };
  responses?: Record<string, OpenApiResponse>;
};

type OpenApiDocument = {
  paths?: Record<string, Partial<Record<string, OpenApiOperation>>>;
  components?: {
    schemas?: Record<string, OpenApiSchema>;
  };
};

type EndpointMeta = {
  groupTitle: string;
  groupDescription: string;
  title: string;
  description: string;
  auth: string;
};

export type ApiReferenceField = {
  name: string;
  type: string;
  required: boolean;
  description: string;
  example: string | null;
  location: "query" | "body";
};

export type ApiReferenceResponse = {
  statusCode: string;
  title: string;
  description: string;
  body: string;
};

export type ApiReferenceEndpoint = {
  id: string;
  title: string;
  description: string;
  method: EndpointMethod;
  path: string;
  auth: string;
  curlExample: string;
  queryParameters: ApiReferenceField[];
  requestFields: ApiReferenceField[];
  requestExample: string | null;
  responses: ApiReferenceResponse[];
};

export type ApiReferenceGroup = {
  title: string;
  description: string;
  endpoints: ApiReferenceEndpoint[];
};

export type ApiReferenceData = {
  groups: ApiReferenceGroup[];
  sourceLabel: string;
  sourceMode: SourceMode;
  baseUrl: string | null;
  unavailableReason: string | null;
};

const GROUP_ORDER = ["Collections", "Payouts", "Checkout", "Operations"];

const ENDPOINT_ORDER = [
  "POST /api/v1/initiate",
  "GET /api/v1/transactions/verify",
  "POST /api/v1/payout",
  "POST /api/v2/complete",
  "POST /api/v2/complete/authorize",
  "POST /webhook/test-signature",
  "GET /public/openapi.json",
];

const DEFAULT_API_BASE_URL = "https://api.yourdomain.com";

const ENDPOINT_METADATA: Record<string, EndpointMeta> = {
  "POST /api/v1/initiate": {
    groupTitle: "Collections",
    groupDescription:
      "Create routed hosted checkout sessions and let RouteX select the healthiest gateway for the payment.",
    title: "Initialize a routed collection",
    description:
      "Creates a hosted checkout session, records the routing decision, and returns the checkout URL plus the selected gateway metadata.",
    auth: "Bearer merchant secret key",
  },
  "GET /api/v1/transactions/verify": {
    groupTitle: "Collections",
    groupDescription:
      "Confirm the normalized outcome of a customer payment from one endpoint, regardless of the underlying PSP.",
    title: "Verify a transaction",
    description:
      "Returns the latest normalized transaction state, selected gateway, gateway reference, and recorded routing attempts.",
    auth: "Bearer merchant secret key",
  },
  "POST /api/v1/payout": {
    groupTitle: "Payouts",
    groupDescription:
      "Disburse funds through the unified payout surface while keeping routing, fees, and gateway references consistent.",
    title: "Create a payout",
    description:
      "Validates wallet balance, chooses an eligible payout gateway, and returns the accepted payout details with routing metadata.",
    auth: "Bearer merchant secret key",
  },
  "POST /api/v2/complete": {
    groupTitle: "Checkout",
    groupDescription:
      "Complete hosted checkout flows that start from the RouteX checkout surface and then fan into channel-specific payment flows.",
    title: "Complete a v2 checkout session",
    description:
      "Takes a pending checkout reference and chosen channel, then advances the checkout into transfer, crypto, or mobile-money execution.",
    auth: "None",
  },
  "POST /api/v2/complete/authorize": {
    groupTitle: "Checkout",
    groupDescription:
      "Authorize follow-up checkout steps like mobile-money OTP confirmation after an initial payment prompt.",
    title: "Authorize a mobile-money checkout",
    description:
      "Confirms a pending mobile-money checkout with the OTP or PIN returned by the provider's challenge step.",
    auth: "None",
  },
  "POST /webhook/test-signature": {
    groupTitle: "Operations",
    groupDescription:
      "Utility endpoints that help you validate integrations, inspect contracts, and generate test payloads while wiring RouteX.",
    title: "Generate a test webhook signature",
    description:
      "Builds a signed test payload so you can validate webhook verification flows before going live.",
    auth: "None",
  },
  "GET /public/openapi.json": {
    groupTitle: "Operations",
    groupDescription:
      "Utility endpoints that help you validate integrations, inspect contracts, and generate test payloads while wiring RouteX.",
    title: "Fetch the public OpenAPI contract",
    description:
      "Returns the sanitized public OpenAPI document that powers the RouteX docs site and public contract tooling.",
    auth: "None",
  },
};

function getGroupTemplate(title: string): ApiReferenceGroup {
  const endpointMeta = Object.values(ENDPOINT_METADATA).find(
    (meta) => meta.groupTitle === title,
  );

  return {
    title,
    description: endpointMeta?.groupDescription ?? "RouteX public API endpoints.",
    endpoints: [],
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

function schemaRefName(ref: string) {
  return ref.split("/").pop() ?? ref;
}

function resolveSchema(
  schema: OpenApiSchema | undefined,
  document: OpenApiDocument,
  seenRefs = new Set<string>(),
): OpenApiSchema | undefined {
  if (!schema) {
    return undefined;
  }

  if (!schema.$ref) {
    return schema;
  }

  const refName = schemaRefName(schema.$ref);
  if (seenRefs.has(refName)) {
    return undefined;
  }

  const nextSeenRefs = new Set(seenRefs);
  nextSeenRefs.add(refName);

  const resolved = document.components?.schemas?.[refName];
  if (!resolved) {
    return undefined;
  }

  return resolveSchema(resolved, document, nextSeenRefs) ?? resolved;
}

function unwrapNullableSchema(
  schema: OpenApiSchema | undefined,
  document: OpenApiDocument,
): OpenApiSchema | undefined {
  const resolved = resolveSchema(schema, document);

  if (!resolved?.anyOf?.length) {
    return resolved;
  }

  const concreteSchema = resolved.anyOf.find(
    (entry) => resolveSchema(entry, document)?.type !== "null",
  );

  return resolveSchema(concreteSchema, document) ?? concreteSchema;
}

function schemaTypeLabel(
  schema: OpenApiSchema | undefined,
  document: OpenApiDocument,
): string {
  const resolved = unwrapNullableSchema(schema, document);

  if (!resolved) {
    return "unknown";
  }

  if (resolved.enum?.length) {
    return resolved.enum.map(String).join(" | ");
  }

  if (resolved.type === "array") {
    return `array<${schemaTypeLabel(resolved.items, document)}>`;
  }

  if (resolved.type === "object") {
    return resolved.title ?? "object";
  }

  if (resolved.format === "email") {
    return "string (email)";
  }

  return resolved.type ?? resolved.title ?? "object";
}

function fallbackScalarExample(
  schema: OpenApiSchema | undefined,
  fieldName: string,
): JsonValue {
  if (!schema) {
    return fieldName.includes("amount") ? 25000 : "string";
  }

  if (schema.enum?.length) {
    return String(schema.enum[0]);
  }

  if (schema.format === "email") {
    return "buyer@example.com";
  }

  if (schema.format === "date-time") {
    return "2026-03-25T12:00:00Z";
  }

  if (schema.type === "boolean") {
    return true;
  }

  if (schema.type === "integer" || schema.type === "number") {
    return fieldName.toLowerCase().includes("amount") ? 25000 : 1;
  }

  if (fieldName.toLowerCase().includes("reference")) {
    return "ORD_1001";
  }

  if (fieldName.toLowerCase().includes("url")) {
    return "https://merchant.example.com/callback";
  }

  return "string";
}

function buildExampleValue(
  schema: OpenApiSchema | undefined,
  document: OpenApiDocument,
  fieldName = "value",
): JsonValue {
  const resolved = unwrapNullableSchema(schema, document);

  if (!resolved) {
    return fallbackScalarExample(undefined, fieldName);
  }

  if (resolved.example !== undefined) {
    return resolved.example as JsonValue;
  }

  if (resolved.default !== undefined) {
    return resolved.default as JsonValue;
  }

  if (resolved.enum?.length) {
    return resolved.enum[0] as JsonValue;
  }

  if (resolved.type === "object" || resolved.properties) {
    const exampleObject: Record<string, JsonValue> = {};
    for (const [propertyName, propertySchema] of Object.entries(
      resolved.properties ?? {},
    )) {
      exampleObject[propertyName] = buildExampleValue(
        propertySchema,
        document,
        propertyName,
      );
    }

    return exampleObject;
  }

  if (resolved.type === "array") {
    return [buildExampleValue(resolved.items, document, `${fieldName}_item`)];
  }

  return fallbackScalarExample(resolved, fieldName);
}

function formatCodeBlock(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function toInlineExample(value: unknown) {
  if (value === null || value === undefined) {
    return null;
  }

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  return JSON.stringify(value);
}

function extractSchemaFields(
  schema: OpenApiSchema | undefined,
  document: OpenApiDocument,
  location: "query" | "body",
  prefix = "",
): ApiReferenceField[] {
  const resolved = unwrapNullableSchema(schema, document);
  if (!resolved?.properties) {
    return [];
  }

  const requiredFields = new Set(resolved.required ?? []);
  const fields: ApiReferenceField[] = [];

  for (const [fieldName, fieldSchema] of Object.entries(resolved.properties)) {
    const path = prefix ? `${prefix}.${fieldName}` : fieldName;
    const unwrappedField = unwrapNullableSchema(fieldSchema, document);
    const description =
      fieldSchema.description ??
      unwrappedField?.description ??
      "No description provided.";

    fields.push({
      name: path,
      type: schemaTypeLabel(fieldSchema, document),
      required: requiredFields.has(fieldName),
      description,
      example: toInlineExample(buildExampleValue(fieldSchema, document, fieldName)),
      location,
    });

    if (unwrappedField?.properties) {
      fields.push(
        ...extractSchemaFields(fieldSchema, document, location, path),
      );
    }
  }

  return fields;
}

function getPreferredJsonMediaType(
  content: Record<string, OpenApiMediaType> | undefined,
) {
  if (!content) {
    return null;
  }

  return (
    content["application/json"] ??
    Object.values(content).find((entry) => Boolean(entry.schema || entry.example)) ??
    null
  );
}

function buildResponseExamples(
  responses: Record<string, OpenApiResponse> | undefined,
  document: OpenApiDocument,
): ApiReferenceResponse[] {
  if (!responses) {
    return [];
  }

  return Object.entries(responses)
    .sort(([left], [right]) => Number(left) - Number(right))
    .map(([statusCode, response]) => {
      const mediaType = getPreferredJsonMediaType(response.content);
      const namedExample = mediaType?.examples
        ? Object.entries(mediaType.examples)[0]
        : null;

      const exampleValue =
        namedExample?.[1]?.value ??
        mediaType?.example ??
        buildExampleValue(mediaType?.schema, document, `response_${statusCode}`);

      return {
        statusCode,
        title: namedExample?.[1]?.summary ?? `HTTP ${statusCode}`,
        description: response.description ?? "No description provided.",
        body: formatCodeBlock(exampleValue),
      };
    });
}

function buildCurlExample(
  method: EndpointMethod,
  path: string,
  auth: string,
  queryParameters: ApiReferenceField[],
  requestExample: string | null,
  baseUrl: string,
) {
  const headerLines: string[] = ['curl --request ' + method + ' \\'];

  headerLines.push(`  --url "${baseUrl}${path}`);

  if (method === "GET" && queryParameters.length > 0) {
    const params = new URLSearchParams();
    for (const parameter of queryParameters) {
      if (parameter.example) {
        params.set(parameter.name, parameter.example);
      }
    }
    headerLines[headerLines.length - 1] += `?${params.toString()}" \\`;
  } else {
    headerLines[headerLines.length - 1] += '" \\';
  }

  if (auth !== "None") {
    headerLines.push('  --header "Authorization: Bearer ROUTEX_TEST_xxx" \\');
  }

  if (method === "POST") {
    headerLines.push('  --header "Content-Type: application/json" \\');
    if (requestExample) {
      headerLines.push(`  --data '${requestExample.replace(/\r?\n/g, "\n")}'`);
    } else {
      headerLines.push("  --data '{}'");
    }
  } else {
    const lastLine = headerLines.pop() ?? "";
    headerLines.push(lastLine.replace(/ \\\\$/, ""));
  }

  return headerLines.join("\n");
}

function getEndpointMeta(method: EndpointMethod, path: string): EndpointMeta {
  return (
    ENDPOINT_METADATA[`${method} ${path}`] ?? {
      groupTitle: path.includes("payout")
        ? "Payouts"
        : path.includes("complete")
          ? "Checkout"
          : "Operations",
      groupDescription: "RouteX public API endpoints.",
      title: `${method} ${path}`,
      description: "Public RouteX API endpoint.",
      auth: path.startsWith("/api/v1/") ? "Bearer merchant secret key" : "None",
    }
  );
}

function compareEndpoints(
  left: ApiReferenceEndpoint,
  right: ApiReferenceEndpoint,
) {
  const leftIndex = ENDPOINT_ORDER.indexOf(`${left.method} ${left.path}`);
  const rightIndex = ENDPOINT_ORDER.indexOf(`${right.method} ${right.path}`);

  if (leftIndex === -1 && rightIndex === -1) {
    return left.path.localeCompare(right.path);
  }

  if (leftIndex === -1) {
    return 1;
  }

  if (rightIndex === -1) {
    return -1;
  }

  return leftIndex - rightIndex;
}

function buildGroupsFromOpenApi(
  document: OpenApiDocument,
  baseUrl: string,
): ApiReferenceGroup[] {
  const groups = Object.fromEntries(
    GROUP_ORDER.map((title) => [title, getGroupTemplate(title)]),
  ) as Record<string, ApiReferenceGroup>;

  for (const [path, operations] of Object.entries(document.paths ?? {})) {
    for (const [methodKey, operation] of Object.entries(operations ?? {})) {
      const method = normalizeOperationMethod(methodKey);
      if (!method || !operation) {
        continue;
      }

      const meta = getEndpointMeta(method, path);
      const requestSchema = getPreferredJsonMediaType(
        operation.requestBody?.content,
      )?.schema;
      const requestExample =
        requestSchema !== undefined
          ? formatCodeBlock(buildExampleValue(requestSchema, document, "payload"))
          : null;

      const queryParameters = (operation.parameters ?? [])
        .filter((parameter) => parameter.in === "query")
        .map((parameter) => ({
          name: parameter.name,
          type: schemaTypeLabel(parameter.schema, document),
          required: Boolean(parameter.required),
          description: parameter.description ?? "No description provided.",
          example: toInlineExample(
            parameter.example ??
              buildExampleValue(parameter.schema, document, parameter.name),
          ),
          location: "query" as const,
        }));

      const endpoint: ApiReferenceEndpoint = {
        id: `${method.toLowerCase()}-${path.replace(/[^\w]+/g, "-")}`,
        title: meta.title,
        description:
          operation.summary ?? operation.description ?? meta.description,
        method,
        path,
        auth: meta.auth,
        curlExample: buildCurlExample(
          method,
          path,
          meta.auth,
          queryParameters,
          requestExample,
          baseUrl,
        ),
        queryParameters,
        requestFields: extractSchemaFields(requestSchema, document, "body"),
        requestExample,
        responses: buildResponseExamples(operation.responses, document),
      };

      groups[meta.groupTitle].endpoints.push(endpoint);
      groups[meta.groupTitle].description = meta.groupDescription;
    }
  }

  return GROUP_ORDER.map((title) => groups[title])
    .map((group) => ({
      ...group,
      endpoints: [...group.endpoints].sort(compareEndpoints),
    }))
    .filter((group) => group.endpoints.length > 0);
}

export async function getApiReferenceData(): Promise<ApiReferenceData> {
  const baseUrl = getApiBaseUrl();

  if (!baseUrl) {
    return {
      groups: [],
      sourceLabel: PUBLIC_OPENAPI_URL,
      sourceMode: "unavailable",
      baseUrl: null,
      unavailableReason:
        "Set ROUTEX_API_BASE_URL so the frontend can fetch the public OpenAPI document from the backend.",
    };
  }

  try {
    const response = await fetch(`${baseUrl}${PUBLIC_OPENAPI_URL}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        groups: [],
        sourceLabel: `${baseUrl}${PUBLIC_OPENAPI_URL}`,
        sourceMode: "unavailable",
        baseUrl,
        unavailableReason:
          "The frontend could not fetch the public OpenAPI document from the backend.",
      };
    }

    const document = (await response.json()) as OpenApiDocument;
    return {
      groups: buildGroupsFromOpenApi(document, baseUrl || DEFAULT_API_BASE_URL),
      sourceLabel: `${baseUrl}${PUBLIC_OPENAPI_URL}`,
      sourceMode: "live",
      baseUrl,
      unavailableReason: null,
    };
  } catch {
    return {
      groups: [],
      sourceLabel: `${baseUrl}${PUBLIC_OPENAPI_URL}`,
      sourceMode: "unavailable",
      baseUrl,
      unavailableReason:
        "The backend is unreachable right now. Confirm the API container is running and ROUTEX_API_BASE_URL points to it.",
    };
  }
}
