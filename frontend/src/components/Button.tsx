import type { ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
}

export function Button({ variant = "primary", className = "", ...rest }: Props) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-card px-5 py-2.5 " +
    "text-base font-medium transition-colors disabled:opacity-50 " +
    "disabled:cursor-not-allowed";
  const styles =
    variant === "primary"
      ? "bg-accent text-white hover:bg-accent-hover"
      : "border border-border bg-surface text-text hover:bg-bg";
  return <button className={`${base} ${styles} ${className}`} {...rest} />;
}
