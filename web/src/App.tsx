import { useCallback, useEffect, useState } from 'react'

import { CatalogSection } from '@/features/catalog/CatalogSection'
import { FeaturedSection } from '@/features/catalog/FeaturedSection'
import { MetricsSection } from '@/features/metrics/MetricsSection'
import { CommandPalette } from '@/features/palette/CommandPalette'
import { ThemeProvider } from '@/lib/theme'
import { Contribute } from '@/sections/Contribute'
import { Footer } from '@/sections/Footer'
import { Header } from '@/sections/Header'
import { Hero } from '@/sections/Hero'
import { HowItWorks } from '@/sections/HowItWorks'

export default function App() {
  const [paletteOpen, setPaletteOpen] = useState(false)
  const openPalette = useCallback(() => setPaletteOpen(true), [])
  const closePalette = useCallback(() => setPaletteOpen(false), [])

  // Catalog query is shared between the hero search form and the catalog.
  const [query, setQuery] = useState('')

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
      {/* First focusable element on the page; revealed on keyboard focus. */}
      <a className="skip-link" href="#main">
        跳到主要内容
      </a>
      <Header onOpenPalette={openPalette} />
      <main id="main" tabIndex={-1}>
        <Hero query={query} onQueryChange={setQuery} />
        <MetricsSection />
        <CatalogSection query={query} onQueryChange={setQuery} />
        <FeaturedSection />
        <HowItWorks />
        <Contribute />
      </main>
      <Footer />
      {paletteOpen ? <CommandPalette onClose={closePalette} /> : null}
    </ThemeProvider>
  )
}
