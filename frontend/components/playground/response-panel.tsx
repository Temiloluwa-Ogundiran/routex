type ResponsePanelProps = {
  isPending: boolean;
  responseBody: string;
};

export function ResponsePanel({
  isPending,
  responseBody,
}: ResponsePanelProps) {
  return (
    <section className="playground-panel">
      <div className="playground-panel__header">
        <div>
          <p className="playground-panel__eyebrow">Response</p>
          <h3>Normalized output</h3>
        </div>
        {isPending ? (
          <span className="playground-status-chip playground-status-chip--pending">
            Sending
          </span>
        ) : (
          <span className="playground-status-chip">Ready</span>
        )}
      </div>
      <pre className="playground-response">{responseBody}</pre>
    </section>
  );
}
