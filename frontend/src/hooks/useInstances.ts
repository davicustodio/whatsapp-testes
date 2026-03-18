import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { getLiveInstances, getLocalInstances, syncInstance } from "../services/api"

export function useLiveInstances(enabled = true) {
  return useQuery({
    queryKey: ["instances", "live"],
    queryFn: getLiveInstances,
    enabled,
  })
}

export function useLocalInstances(enabled = true) {
  return useQuery({
    queryKey: ["instances", "local"],
    queryFn: getLocalInstances,
    enabled,
  })
}

export function useSyncInstance() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (instanceName: string) => syncInstance(instanceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["instances"] })
    },
  })
}
