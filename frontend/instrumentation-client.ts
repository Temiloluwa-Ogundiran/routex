import posthog from "posthog-js";

const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY?.trim();
const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST?.trim();
const posthogClient = posthog as typeof posthog & {
  __loaded?: boolean;
};

if (
  typeof window !== "undefined" &&
  posthogKey &&
  posthogHost &&
  !posthogClient.__loaded
) {
  posthog.init(posthogKey, {
    api_host: posthogHost,
    autocapture: true,
    capture_pageview: true,
  });
  (
    window as Window & {
      posthog?: typeof posthog;
    }
  ).posthog = posthog;
}
