import { create } from "zustand"

type InstanceState = {
  selectedInstance: string | null
  setSelectedInstance: (instanceName: string) => void
  clear: () => void
}

const selectedFromStorage = localStorage.getItem("wt_instance")

export const useInstanceStore = create<InstanceState>((set) => ({
  selectedInstance: selectedFromStorage,
  setSelectedInstance: (instanceName) => {
    localStorage.setItem("wt_instance", instanceName)
    set({ selectedInstance: instanceName })
  },
  clear: () => {
    localStorage.removeItem("wt_instance")
    set({ selectedInstance: null })
  },
}))
