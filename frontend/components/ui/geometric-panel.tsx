type GeometricPanelProps = {
  caption: string;
  title: string;
  detail: string;
};

export function GeometricPanel({ caption, title, detail }: GeometricPanelProps) {
  return (
    <aside className="geometric-panel" aria-label={title}>
      <div className="geometric-panel__art" aria-hidden="true">
        <svg viewBox="0 0 480 360" preserveAspectRatio="none">
          <defs>
            <pattern id="rx-grid" width="24" height="24" patternUnits="userSpaceOnUse">
              <path d="M24 0H0V24" fill="none" stroke="currentColor" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="480" height="360" fill="url(#rx-grid)" />
          <circle cx="240" cy="170" r="88" fill="none" stroke="currentColor" strokeWidth="2" />
          <circle cx="240" cy="170" r="42" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="M120 276L240 100L360 276Z" fill="none" stroke="currentColor" strokeWidth="2" />
        </svg>
      </div>

      <div className="geometric-panel__copy">
        <p className="dashboard-card__eyebrow">{caption}</p>
        <h3>{title}</h3>
        <p>{detail}</p>
      </div>
    </aside>
  );
}
