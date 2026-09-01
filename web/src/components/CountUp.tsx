import { useEffect, useRef, useState } from 'react'

import { useInView } from '@/lib/useInView'
import { useMediaQuery } from '@/lib/useMediaQuery'

// Matches --amicro-duration-section (480ms).
const COUNT_UP_DURATION_MS = 480

interface CountUpProps {
  value: number
}

/** Counts up to `value` once when scrolled into view; reduced motion shows the final value. */
export function CountUp({ value }: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const reducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    if (!inView) {
      return
    }
    if (reducedMotion || value <= 0) {
      setDisplay(value)
      return
    }
    let frame = 0
    const start = performance.now()
    const tick = (now: number) => {
      const progress = Math.min((now - start) / COUNT_UP_DURATION_MS, 1)
      // easeOutCubic keeps the motion calm and interruptible.
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(eased * value))
      if (progress < 1) {
        frame = requestAnimationFrame(tick)
      }
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [inView, reducedMotion, value])

  return <span ref={ref}>{display}</span>
}
