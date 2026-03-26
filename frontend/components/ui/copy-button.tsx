"use client";

import { useState } from "react";

type CopyButtonProps = {
  className?: string;
  copiedLabel?: string;
  label?: string;
  value: string;
};

export function CopyButton({
  className,
  copiedLabel = "Copied",
  label = "Copy",
  value,
}: CopyButtonProps) {
  const [buttonLabel, setButtonLabel] = useState(label);

  async function handleCopy() {
    if (!navigator.clipboard?.writeText) {
      setButtonLabel("Unavailable");
      window.setTimeout(() => setButtonLabel(label), 1400);
      return;
    }

    await navigator.clipboard.writeText(value);
    setButtonLabel(copiedLabel);
    window.setTimeout(() => setButtonLabel(label), 1400);
  }

  return (
    <button
      className={`copy-button${className ? ` ${className}` : ""}`}
      onClick={() => void handleCopy()}
      type="button"
    >
      {buttonLabel}
    </button>
  );
}
