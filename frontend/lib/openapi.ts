import { getApiBaseUrl, getPublicApiBaseUrl } from "./runtime-config";

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

const GROUP_ORDER = ["Collections", "Payouts"];

const ENDPOINT_ORDER = [
  "POST /api/v1/initiate",
  "GET /api/v1/transactions/verify",
  "POST /api/v1/payout",
];

const DEFAULT_API_BASE_URL = "https://routexapi.xoroai.cloud";

const ENDPOINT_METADATA: Record<string, EndpointMeta> = {
  "POST /api/v1/initiate": {
    groupTitle: "Collections",
    groupDescription:
      "Accept payments in test mode with one clean hosted-checkout flow and normalized RouteX responses.",
    title: "Initialize a routed collection",
    description:
      "Create a hosted checkout session, optionally force a specific gateway, and receive a single RouteX checkout URL with routing metadata. If you include notification_url, RouteX will send normalized payment webhooks there after provider confirmation.",
    auth: "Bearer secret key",
  },
  "GET /api/v1/transactions/verify": {
    groupTitle: "Collections",
    groupDescription:
      "Confirm the final customer payment state through one normalized verification endpoint.",
    title: "Verify a transaction",
    description:
      "Fetch the latest RouteX status, selected gateway, gateway reference, and routed attempt history for a transaction reference.",
    auth: "Bearer secret key",
  },
  "POST /api/v1/payout": {
    groupTitle: "Payouts",
    groupDescription:
      "Send funds through the unified payout surface while keeping routing, fees, and references consistent.",
    title: "Create a payout",
    description:
      "Validate wallet balance, choose an eligible payout gateway, and return the accepted payout details with routing metadata.",
    auth: "Bearer secret key",
  },
};

const FIELD_DESCRIPTION_OVERRIDES: Record<string, string> = {
  amount:
    "Amount in the customer-facing currency unit. Example: send 2500 to charge NGN 2,500. RouteX converts internally for gateways that require minor units.",
  currency: "Currency code for this request. The current MVP supports NGN.",
  customer: "Customer details for the payment.",
  "customer.email": "Customer email address.",
  "customer.name": "Optional customer display name.",
  destination: "Destination bank account details for the payout.",
  "destination.account_number": "Destination bank account number.",
  "destination.bank_code": "Destination bank code.",
  gateway_code:
    "Optional gateway override. Omit this field to let RouteX choose automatically.",
  metadata: "Optional metadata object returned with the transaction.",
  mode: "Preferred payment channel for the checkout experience.",
  narration: "Optional text shown to the customer or receiving gateway.",
  notification_url:
    "Your server webhook URL. RouteX sends normalized charge or payout events here after payment confirmation.",
  redirect_url: "Where RouteX should return the customer after checkout.",
  reference: "Your unique merchant reference for this request.",
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

function getFieldDescription(fieldName: string, description: string | undefined) {
  if (description && description !== "No description provided.") {
    return description;
  }

  return FIELD_DESCRIPTION_OVERRIDES[fieldName] ?? "";
}

function extractSchemaFields(
  schema: OpenApiSchema | undefined,
  document: OpenApiDocument,
  location: "query" | "body",
): ApiReferenceField[] {
  const resolved = unwrapNullableSchema(schema, document);
  if (!resolved?.properties) {
    return [];
  }

  const requiredFields = new Set(resolved.required ?? []);
  const fields: ApiReferenceField[] = [];

  for (const [fieldName, fieldSchema] of Object.entries(resolved.properties)) {
    fields.push({
      name: fieldName,
      type: schemaTypeLabel(fieldSchema, document),
      required: requiredFields.has(fieldName),
      description: getFieldDescription(
        fieldName,
        fieldSchema.description ?? unwrapNullableSchema(fieldSchema, document)?.description,
      ),
      example: toInlineExample(buildExampleValue(fieldSchema, document, fieldName)),
      location,
    });
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
        description: response.description ?? "RouteX response payload.",
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
        : "Collections",
      groupDescription: "RouteX public API endpoints.",
      title: `${method} ${path}`,
      description: "Public RouteX API endpoint.",
      auth: path.startsWith("/api/v1/") ? "Bearer secret key" : "None",
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
      if (!ENDPOINT_ORDER.includes(`${method} ${path}`)) {
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
          description: getFieldDescription(parameter.name, parameter.description),
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
  const publicBaseUrl = getPublicApiBaseUrl();

  if (!baseUrl) {
    return {
      groups: [],
      sourceLabel: PUBLIC_OPENAPI_URL,
      sourceMode: "unavailable",
      baseUrl: publicBaseUrl,
      unavailableReason:
        "The public API reference is not connected yet. Set the backend URL and reload this page.",
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
          "We could not load the public API reference right now.",
      };
    }

    const document = (await response.json()) as OpenApiDocument;
    return {
      groups: buildGroupsFromOpenApi(
        document,
        publicBaseUrl || baseUrl || DEFAULT_API_BASE_URL,
      ),
      sourceLabel: `${publicBaseUrl || baseUrl}${PUBLIC_OPENAPI_URL}`,
      sourceMode: "live",
      baseUrl: publicBaseUrl || baseUrl,
      unavailableReason: null,
    };
  } catch {
    return {
      groups: [],
      sourceLabel: `${publicBaseUrl || baseUrl}${PUBLIC_OPENAPI_URL}`,
      sourceMode: "unavailable",
      baseUrl: publicBaseUrl || baseUrl,
      unavailableReason:
        "We could not reach the API right now. Please try again shortly.",
    };
  }
}
