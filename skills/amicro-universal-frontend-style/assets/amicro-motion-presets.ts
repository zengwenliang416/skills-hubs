/** Framework-neutral Amicro motion constants and small helpers. No runtime dependency. */
export const AMICRO_EASE = [0.16, 1, 0.3, 1] as const;
export const AMICRO_CURTAIN_EASE = [0.83, 0, 0.17, 1] as const;

export const AMICRO_DURATION = {
  instant: 0.12,
  fast: 0.18,
  control: 0.24,
  card: 0.32,
  section: 0.48,
  route: 0.65,
} as const;

export const AMICRO_SPRING = {
  crisp: { stiffness: 600, damping: 25 },
  layout: { stiffness: 500, damping: 25 },
  gentle: { stiffness: 400, damping: 25 },
  ring: { stiffness: 600, damping: 15 },
} as const;

export function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
}

export type MagneticOffset = { x: number; y: number };

export function magneticOffset(
  event: Pick<PointerEvent, "clientX" | "clientY">,
  element: Element,
  strength = 0.25,
  maxDistance = 12,
): MagneticOffset {
  const rect = element.getBoundingClientRect();
  const x = (event.clientX - (rect.left + rect.width / 2)) * strength;
  const y = (event.clientY - (rect.top + rect.height / 2)) * strength;
  const clamp = (value: number) => Math.max(-maxDistance, Math.min(maxDistance, value));
  return { x: clamp(x), y: clamp(y) };
}
