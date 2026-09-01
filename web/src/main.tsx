import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import './styles/amicro-tokens.css'
import './styles/hub-tokens.css'
import './styles/base.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('Root container #root is missing in index.html')
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
