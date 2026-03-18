import type { HTMLAttributes } from "react"

import { cn } from "../../lib/utils"

type BadgeVariant = "default" | "success" | "warning" | "danger"

const badgeClass: Record<BadgeVariant, string> = {
  default: "bg-[#1d2a50] text-[#dbe3ff]",
  success: "bg-emerald-500/20 text-emerald-300",
  warning: "bg-amber-500/20 text-amber-300",
  danger: "bg-rose-500/20 text-rose-300",
}

export function Badge({
  className,
  variant = "default",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", badgeClass[variant], className)}
      {...props}
    />
  )
}
