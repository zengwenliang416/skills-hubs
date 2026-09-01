import { useEffect, useState } from 'react'
import type { RefObject } from 'react'

import { useInView } from './useInView'

/**
 * Whether ambient/looping animation should run for the referenced element:
 * only while it is on screen and the page is visible.
 */
export function useAmbientActive(ref: RefObject<Element | null>): boolean {
  const inView = useInView(ref)
  const [pageVisible, setPageVisible] = useState(() =>
    typeof document === 'undefined' ? true : !document.hidden,
  )

  useEffect(() => {
    const onVisibilityChange = () => setPageVisible(!document.hidden)
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => document.removeEventListener('visibilitychange', onVisibilityChange)
  }, [])

  return inView && pageVisible
}
