import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.tsx'
import { AuthProvider } from './auth.tsx'
import { CatalogueProvider } from './catalogue.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <CatalogueProvider>
          <App />
        </CatalogueProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
