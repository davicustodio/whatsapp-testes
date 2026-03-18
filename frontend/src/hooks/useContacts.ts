import { useQuery } from "@tanstack/react-query"

import { getContacts } from "../services/api"

export function useContacts(instanceName: string | null) {
  return useQuery({
    queryKey: ["contacts", instanceName],
    queryFn: () => getContacts(instanceName as string),
    enabled: Boolean(instanceName),
  })
}
