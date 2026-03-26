import { CopyButton } from "../ui/copy-button";

type RequestPanelProps = {
  body: string;
  description: string;
  endpoint: string;
  method: string;
  statusLabel: string;
  onBodyChange: (value: string) => void;
};

export function RequestPanel({
  body,
  description,
  endpoint,
  method,
  statusLabel,
  onBodyChange,
}: RequestPanelProps) {
  return (
    <section className="playground-panel">
      <div className="playground-panel__header">
        <div>
          <p className="playground-panel__eyebrow">Request</p>
          <h3>
            {method} {endpoint}
          </h3>
        </div>
        <span className="playground-status-chip">{statusLabel}</span>
      </div>
      <p className="playground-panel__description">{description}</p>
      <div className="playground-panel__toolbar">
        <CopyButton value={body} />
      </div>
      <textarea
        aria-label="Request payload"
        className="playground-textarea"
        onChange={(event) => onBodyChange(event.target.value)}
        spellCheck={false}
        value={body}
      />
    </section>
  );
}
