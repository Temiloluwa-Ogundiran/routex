export function BrowserMockup() {
  return (
    <section aria-label="RouteX launch card" className="acid-showcase">
      <article className="acid-showcase__deal">
        <span>One dashboard</span>
        <strong>See every payment in one place.</strong>
      </article>

      <article className="acid-showcase__frame">
        <div aria-hidden="true" className="acid-showcase__art" />
        <div className="acid-showcase__footer">
          <span className="acid-showcase__tag">Live</span>
          <div>
            <strong>RouteX flow</strong>
            <p>Pay, track, and confirm from one simple setup.</p>
          </div>
          <span aria-hidden="true">-&gt;</span>
        </div>
      </article>
    </section>
  );
}
