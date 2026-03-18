import { useMutation } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { toast } from "sonner"

import { Button } from "../components/ui/button"
import { Card } from "../components/ui/card"
import { Textarea } from "../components/ui/textarea"
import { useContacts } from "../hooks/useContacts"
import { sendBatch } from "../services/api"
import { useInstanceStore } from "../stores/instanceStore"

export function BatchSendPage() {
  const { selectedInstance } = useInstanceStore()
  const contactsQuery = useContacts(selectedInstance)
  const [selected, setSelected] = useState<Record<string, boolean>>({})
  const [text, setText] = useState("")

  const selectedRecipients = useMemo(() => {
    const contacts = contactsQuery.data ?? []
    return contacts
      .filter((contact) => selected[contact.id])
      .map((contact) => contact.phone_number || contact.remote_jid.split("@")[0])
  }, [contactsQuery.data, selected])

  const mutation = useMutation({
    mutationFn: () => sendBatch(selectedInstance as string, selectedRecipients, text),
    onSuccess: (data) => toast.success(`Envio em lote concluido: ${data.sent}/${data.total}`),
    onError: () => toast.error("Falha no envio em lote."),
  })

  if (!selectedInstance) {
    return <p className="text-sm text-muted">Selecione uma instancia no dashboard primeiro.</p>
  }

  return (
    <div className="grid gap-4 md:grid-cols-[1fr_360px]">
      <Card>
        <h3 className="font-display text-lg">Escolha os contatos</h3>
        <div className="mt-3 max-h-[420px] space-y-2 overflow-y-auto pr-1">
          {(contactsQuery.data ?? []).map((contact) => (
            <label
              key={contact.id}
              className="flex cursor-pointer items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:border-accent/60"
            >
              <input
                type="checkbox"
                checked={Boolean(selected[contact.id])}
                onChange={(event) => {
                  setSelected((prev) => ({ ...prev, [contact.id]: event.target.checked }))
                }}
              />
              <span className="text-text">{contact.push_name || contact.phone_number || contact.remote_jid}</span>
            </label>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="font-display text-lg">Mensagem em lote</h3>
        <p className="mt-1 text-sm text-muted">Selecionados: {selectedRecipients.length}</p>
        <div className="mt-3 space-y-3">
          <Textarea
            placeholder="Escreva a mensagem que sera enviada para todos selecionados"
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          <Button
            className="w-full"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || selectedRecipients.length === 0 || !text.trim()}
          >
            Enviar para selecionados
          </Button>
        </div>
      </Card>
    </div>
  )
}
