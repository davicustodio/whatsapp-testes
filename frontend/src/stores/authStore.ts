import { create } from "zustand"

type AuthState = {
  token: string | null
  setToken: (token: string | null) => void
  logout: () => void
}

const tokenFromStorage = localStorage.getItem("wt_token")

export const useAuthStore = create<AuthState>((set) => ({
  token: tokenFromStorage,
  setToken: (token) => {
    if (token) localStorage.setItem("wt_token", token)
    else localStorage.removeItem("wt_token")
    set({ token })
  },
  logout: () => {
    localStorage.removeItem("wt_token")
    set({ token: null })
  },
}))
