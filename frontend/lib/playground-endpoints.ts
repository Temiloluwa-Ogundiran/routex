export type PlaygroundEndpointId = "initiate" | "verify" | "payout";

export type PlaygroundEndpoint = {
  id: PlaygroundEndpointId;
  label: string;
  method: "GET" | "POST";
  path: string;
  description: string;
  requestTemplate: Record<string, unknown>;
};

export const PLAYGROUND_ENDPOINTS: PlaygroundEndpoint[] = [
  {
    id: "initiate",
    label: "Initiate",
    method: "POST",
    path: "/api/v1/initiate",
    description: "Create a sandbox collection and return a hosted checkout URL.",
    requestTemplate: {
      reference: "ORD_1001",
      amount: 25000,
      currency: "NGN",
      gateway_code: "pstk",
      customer: {
        email: "buyer@example.com",
        name: "Ada Obi",
      },
      redirect_url: "https://merchant.example.com/return",
      notification_url: "https://merchant.example.com/webhook",
      mode: "card",
    },
  },
  {
    id: "verify",
    label: "Verify",
    method: "GET",
    path: "/api/v1/transactions/verify",
    description: "Check the normalized status of an existing transaction reference via query string.",
    requestTemplate: {
      reference: "ORD_1001",
    },
  },
  {
    id: "payout",
    label: "Payout",
    method: "POST",
    path: "/api/v1/payout",
    description: "Trigger a sandbox payout request through the unified payout surface.",
    requestTemplate: {
      reference: "PO_9001",
      amount: 15000,
      currency: "NGN",
      destination: {
        bank_code: "058",
        account_number: "0123456789",
      },
      narration: "Vendor payout",
    },
  },
];

export const ALLOWED_PLAYGROUND_ENDPOINTS = PLAYGROUND_ENDPOINTS.map(
  (endpoint) => endpoint.path,
);

export function getPlaygroundEndpoint(id: PlaygroundEndpointId) {
  return PLAYGROUND_ENDPOINTS.find((endpoint) => endpoint.id === id);
}
