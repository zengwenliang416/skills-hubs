import { useMediaQuery } from './useMediaQuery'

/**
 * True only when pointer-driven motion enhancements are appropriate:
 * hover-capable fine pointer AND no reduced-motion request. Pointer
 * listeners (tilt, magnetic) must not be attached when this is false.
 */
export function useFinePointerMotion(): boolean {
  const hoverFine = useMediaQuery('(hover: hover) and (pointer: fine)')
  const motionAllowed = useMediaQuery('(prefers-reduced-motion: no-preference)')
  return hoverFine && motionAllowed
}
