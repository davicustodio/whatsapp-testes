import { useMemo, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { toast } from "sonner"

import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Textarea } from "../components/ui/textarea"
import { useChats } from "../hooks/useChats"
import { useMessages, useSendMessage } from "../hooks/useMessages"
import { formatPhone } from "../lib/utils"
import { useInstanceStore } from "../stores/instanceStore"

export function ChatPage() {
  const { selectedInstance } = useInstanceStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const chatJid = searchParams.get("jid")

  const chatsQuery = useChats(selectedInstance)
  const messagesQuery = useMessages(selectedInstance, chatJid)
  const sendMutation = useSendMessage(selectedInstance, chatJid)

  const [messageText, setMessageText] = useState("")
  const [manualNumber, setManualNumber] = useState("")

  const chats = chatsQuery.data ?? []
  const selectedChat = chats.find((chat) => chat.remote_jid === chatJid)

  const chatTarget = useMemo(() => {
    if (manualNumber.trim()) return manualNumber
    return selectedChat?.remote_jid ?? ""
  }, [manualNumber, selectedChat])

  if (!selectedInstance) {
    return <p className="text-sm text-muted">Selecione uma instancia no dashboard primeiro.</p>
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
      <aside className="rounded-xl border border-border bg-[#111933] p-3">
        <h3 className="mb-2 text-sm font-semibold text-text">Chats</h3>
        <div className="space-y-2">
          {chats.map((chat) => {
            const active = chat.remote_jid === chatJid
            return (
              <button
                key={chat.id}
                onClick={() => setSearchParams({ jid: chat.remote_jid })}
                className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                  active ? "border-accent bg-accentSoft" : "border-border hover:border-accent/50"
                }`}
              >
                <p className="text-sm text-text">{chat.chat_name || chat.remote_jid}</p>
                <div className="mt-1 flex items-center justify-between">
                  <p className="text-xs text-muted">{chat.remote_jid}</p>
                  {chat.unread_count > 0 && <Badge>{chat.unread_count}</Badge>}
                </div>
              </button>
            )
          })}
        </div>
      </aside>

      <section className="rounded-xl border border-border bg-[#111933] p-3">
        <div className="mb-3">
          <p className="text-sm text-muted">Destino atual</p>
          <p className="text-text">{chatTarget || "selecione um chat ou digite numero manual"}</p>
        </div>

        <div className="h-[360px] space-y-2 overflow-y-auto rounded-xl border border-border bg-[#0b1122] p-3">
          {(messagesQuery.data ?? []).map((message) => (
            <div
              key={message.id}
              className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                message.from_me ? "ml-auto bg-accentSoft text-text" : "bg-panel text-text"
              }`}
            >
              <p>{message.content || "(mensagem sem texto)"}</p>
              <p className="mt-1 text-[11px] text-muted">{new Date(message.timestamp).toLocaleString()}</p>
            </div>
          ))}
        </div>

        <div className="mt-3 space-y-2">
          <Input
            placeholder="Numero aberto (opcional), ex: 5511999999999"
            value={manualNumber}
            onChange={(event) => setManualNumber(event.target.value)}
          />
          <Textarea placeholder="Escreva sua mensagem de teste" value={messageText} onChange={(event) => setMessageText(event.target.value)} />
          <div className="flex justify-end">
            <Button
              onClick={async () => {
                if (!chatTarget || !messageText.trim()) {
                  toast.error("Informe um destino e o texto da mensagem.")
                  return
                }
                try {
                  await sendMutation.mutateAsync({
                    number: formatPhone(chatTarget),
                    text: messageText.trim(),
                  })
                  toast.success("Mensagem enviada.")
                  setMessageText("")
                } catch {
                  toast.error("Falha ao enviar mensagem.")
                }
              }}
              disabled={sendMutation.isPending}
            >
              Enviar mensagem
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
