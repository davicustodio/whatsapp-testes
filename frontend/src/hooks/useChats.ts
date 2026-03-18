import { useQuery } from "@tanstack/react-query"

import { getChats } from "../services/api"

export function useChats(instanceName: string | null) {
  return useQuery({
    queryKey: ["chats", instanceName],
    queryFn: () => getChats(instanceName as string),
    enabled: Boolean(instanceName),
  })
}
