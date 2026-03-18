import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPhone(number: string) {
  const digits = number.replace(/\D/g, "")
  if (digits.length < 8) return number
  return `+${digits}`
}
