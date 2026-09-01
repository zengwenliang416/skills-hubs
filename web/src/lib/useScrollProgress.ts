// Ported from @subhanhq/amicro (MIT) — https://github.com/Subhan-code/Amicro--Micro-transitions-
import { useEffect, useState } from 'react'
import type { RefObject } from 'react'

/**
 * Scroll progress (0–1) of the window, or of the referenced scroll container.
 * Used as a state indicator, so it stays active under reduced motion.
 */
export function useScrollProgress(ref?: RefObject<HTMLElement | null>): number {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let pendingFrame = 0

    const readProgress = () => {
      pendingFrame = 0
      if (ref?.current) {
        const element = ref.current
        const totalHeight = element.scrollHeight - element.clientHeight
        setProgress(totalHeight === 0 ? 0 : element.scrollTop / totalHeight)
      } else {
        const totalHeight = document.documentElement.scrollHeight - window.innerHeight
        setProgress(totalHeight === 0 ? 0 : window.scrollY / totalHeight)
      }
    }

    // Throttle scroll events to one state update per animation frame.
    const handleScroll = () => {
      if (pendingFrame === 0) {
        pendingFrame = window.requestAnimationFrame(readProgress)
      }
    }

    const target: HTMLElement | Window = ref?.current ?? window
    target.addEventListener('scroll', handleScroll, { passive: true })
    readProgress()

    return () => {
      target.removeEventListener('scroll', handleScroll)
      if (pendingFrame !== 0) {
        window.cancelAnimationFrame(pendingFrame)
      }
    }
  }, [ref])

  return progress
}
