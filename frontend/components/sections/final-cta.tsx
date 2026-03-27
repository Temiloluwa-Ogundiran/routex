import Link from "next/link";
import { DOCS_LINK_REL, DOCS_LINK_TARGET, docsHref } from "../../lib/docs-url";

export function FinalCta() {
  return (
    <section className="acid-final-cta" id="docs">
      <div className="acid-final-cta__panel">
        <p className="feature-block__eyebrow">Start here</p>
        <h2 className="acid-final-cta__title">Start in minutes.</h2>
        <p className="acid-final-cta__copy">
          Create your workspace, test a payment, then go live when you are ready.
        </p>
        <div className="acid-final-cta__actions">
          <Link className="push-button push-button--primary" href="/signup">
            Get started
          </Link>
          <a
            className="push-button push-button--secondary"
            href={docsHref()}
            rel={DOCS_LINK_REL}
            target={DOCS_LINK_TARGET}
          >
            Read docs
          </a>
        </div>
      </div>
    </section>
  );
}
