import type { HTMLAttributes } from "react"

import { cn } from "../../lib/utils"

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-panel/85 p-4 shadow-[0_10px_35px_rgba(0,0,0,0.22)]",
        className,
      )}
      {...props}
    />
  )
}
