import { useCallback, useEffect, useState } from 'react'

import { CatalogSection } from '@/features/catalog/CatalogSection'
import { FeaturedSection } from '@/features/catalog/FeaturedSection'
import { MetricsSection } from '@/features/metrics/MetricsSection'
import { CommandPalette } from '@/features/palette/CommandPalette'
import { ThemeProvider } from '@/lib/theme'
import { Footer } from '@/sections/Footer'
import { Header } from '@/sections/Header'
import { Hero } from '@/sections/Hero'

export default function App() {
  const [paletteOpen, setPaletteOpen] = useState(false)
  const openPalette = useCallback(() => setPaletteOpen(true), [])
  const closePalette = useCallback(() => setPaletteOpen(false), [])

  // Global ⌘K / Ctrl+K opens the palette (it self-handles the toggle-off).
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <ThemeProvider>
      <Header onOpenPalette={openPalette} />
      <main>
        <Hero />
        <MetricsSection />
        <CatalogSection />
        <FeaturedSection />
      </main>
      <Footer />
      {paletteOpen ? <CommandPalette onClose={closePalette} /> : null}
    </ThemeProvider>
  )
}
