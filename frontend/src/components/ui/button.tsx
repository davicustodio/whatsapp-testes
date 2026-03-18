import type { ButtonHTMLAttributes } from "react"

import { cn } from "../../lib/utils"

type Variant = "primary" | "secondary" | "ghost" | "danger"

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant
}

const variants: Record<Variant, string> = {
  primary:
    "bg-accent text-slate-950 border border-transparent hover:opacity-90 disabled:opacity-50",
  secondary:
    "bg-panel border border-border text-text hover:bg-[#161e3b] disabled:opacity-50",
  ghost: "bg-transparent border border-transparent text-muted hover:text-text hover:bg-[#11182f]",
  danger: "bg-danger/90 text-white border border-danger hover:bg-danger disabled:opacity-50",
}

export function Button({ className, variant = "primary", ...props }: Props) {
  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-xl px-4 text-sm font-semibold transition",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent",
        variants[variant],
        className,
      )}
      {...props}
    />
  )
}
