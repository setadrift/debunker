import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (auth: { user: User; token: string }) => void
  logout: () => void
  initFromStorage: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: ({ user, token }) =>
        set({
          user,
          token,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        }),
      initFromStorage: () => {
        const stored = localStorage.getItem("jwt")
        if (stored) {
          set({ token: stored })
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
)

// Subscribe to token changes and persist to localStorage
useAuthStore.subscribe((state) => {
  if (state.token) {
    localStorage.setItem("jwt", state.token)
  } else {
    localStorage.removeItem("jwt")
  }
}) 