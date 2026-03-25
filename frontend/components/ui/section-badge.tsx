type SectionBadgeProps = {
  children: React.ReactNode;
};

export function SectionBadge({ children }: SectionBadgeProps) {
  return <span className="section-badge">{children}</span>;
}
