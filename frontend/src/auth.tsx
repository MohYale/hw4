import { createContext, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { Shopper } from './types.ts'

const STORAGE_KEY = 'campus-customs-shopper'

type AuthValue = {
  shopper: Shopper | null
  setShopper: (shopper: Shopper | null) => void
}

const AuthContext = createContext<AuthValue | null>(null)

function readShopper(): Shopper | null {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }
  try {
    return JSON.parse(raw) as Shopper
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [shopper, setShopperState] = useState<Shopper | null>(readShopper)

  const value = useMemo<AuthValue>(
    () => ({
      shopper,
      setShopper(next) {
        setShopperState(next)
        if (next) {
          sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
        } else {
          sessionStorage.removeItem(STORAGE_KEY)
        }
      },
    }),
    [shopper],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return value
}
