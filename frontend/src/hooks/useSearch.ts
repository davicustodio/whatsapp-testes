import { useMutation } from "@tanstack/react-query"

import { semanticSearch } from "../services/api"

export function useSemanticSearch(instanceName: string | null) {
  return useMutation({
    mutationFn: ({ query, limit = 10 }: { query: string; limit?: number }) =>
      semanticSearch(instanceName as string, query, limit),
  })
}
