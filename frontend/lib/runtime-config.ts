export function getApiBaseUrl() {
  return process.env.ROUTEX_API_BASE_URL ?? null;
}

export function getPublicApiBaseUrl() {
  return process.env.SERVER_URL ?? "https://routexapi.xoroai.cloud";
}

export function getPlaygroundSecretKey() {
  return process.env.ROUTEX_PLAYGROUND_SECRET_KEY ?? null;
}

export function isLivePlaygroundConfigured() {
  return Boolean(getApiBaseUrl() && getPlaygroundSecretKey());
}
