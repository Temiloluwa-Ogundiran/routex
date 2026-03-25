import { PushButton } from "../ui/push-button";

export function FinalCta() {
  return (
    <section className="story-section story-section--cta" id="docs">
      <div className="final-cta">
        <h2>READY TO ROUTE SMARTER?</h2>
        <p>
          Test collections, payouts, and verification in the RouteX sandbox
          before you wire in production.
        </p>
        <div className="hero-actions">
          <PushButton>Start in Sandbox</PushButton>
          <PushButton variant="secondary">View API Docs</PushButton>
        </div>
      </div>
    </section>
  );
}
