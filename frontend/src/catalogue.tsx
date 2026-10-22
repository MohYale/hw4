import { createContext, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { ProductMatch } from './types.ts'

type CatalogueValue = {
  query: string
  matches: ProductMatch[] | null
  setMatches: (query: string, matches: ProductMatch[]) => void
  clearMatches: () => void
}

const CatalogueContext = createContext<CatalogueValue | null>(null)

export function CatalogueProvider({ children }: { children: ReactNode }) {
  const [query, setQuery] = useState('')
  const [matches, setMatchList] = useState<ProductMatch[] | null>(null)

  const value = useMemo<CatalogueValue>(
    () => ({
      query,
      matches,
      setMatches(nextQuery, nextMatches) {
        setQuery(nextQuery)
        setMatchList(nextMatches)
      },
      clearMatches() {
        setQuery('')
        setMatchList(null)
      },
    }),
    [matches, query],
  )

  return <CatalogueContext.Provider value={value}>{children}</CatalogueContext.Provider>
}

export function useCatalogue(): CatalogueValue {
  const value = useContext(CatalogueContext)
  if (!value) {
    throw new Error('useCatalogue must be used inside CatalogueProvider')
  }
  return value
}
