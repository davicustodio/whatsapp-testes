import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { getMessages, sendMessage } from "../services/api"

export function useMessages(instanceName: string | null, chatJid: string | null) {
  return useQuery({
    queryKey: ["messages", instanceName, chatJid],
    queryFn: () => getMessages(instanceName as string, chatJid as string),
    enabled: Boolean(instanceName && chatJid),
  })
}

export function useSendMessage(instanceName: string | null, chatJid: string | null) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ number, text }: { number: string; text: string }) =>
      sendMessage(instanceName as string, number, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", instanceName, chatJid] })
      queryClient.invalidateQueries({ queryKey: ["chats", instanceName] })
    },
  })
}
