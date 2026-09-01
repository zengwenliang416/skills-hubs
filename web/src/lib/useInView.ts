import { useEffect, useState } from 'react'
import type { RefObject } from 'react'

interface UseInViewOptions {
  /** Observe only until the first intersection, then disconnect. */
  once?: boolean
  threshold?: number
}

/** Observe an element's intersection with the viewport. */
export function useInView(ref: RefObject<Element | null>, options: UseInViewOptions = {}): boolean {
  const { once = false, threshold = 0.2 } = options
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element || typeof IntersectionObserver === 'undefined') {
      // Without observer support, treat as visible so content is never hidden.
      setInView(true)
      return
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (!entry) {
          return
        }
        setInView(entry.isIntersecting)
        if (once && entry.isIntersecting) {
          observer.disconnect()
        }
      },
      { threshold },
    )
    observer.observe(element)
    return () => observer.disconnect()
  }, [ref, once, threshold])

  return inView
}
