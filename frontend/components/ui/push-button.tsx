type PushButtonProps = {
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
  variant?: "primary" | "secondary";
  type?: "button" | "submit";
};

export function PushButton({
  children,
  className,
  disabled = false,
  onClick,
  variant = "primary",
  type = "button",
}: PushButtonProps) {
  return (
    <button
      className={`push-button push-button--${variant}${className ? ` ${className}` : ""}`}
      disabled={disabled}
      onClick={onClick}
      type={type}
    >
      {children}
    </button>
  );
}
