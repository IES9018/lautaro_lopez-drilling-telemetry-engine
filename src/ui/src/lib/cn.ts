import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Convierte rad/s → rpm. */
export function radSToRpm(omega: number): number {
  return (omega * 60) / (2 * Math.PI);
}
