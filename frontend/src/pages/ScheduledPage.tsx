import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { toast } from "sonner"

import { Button } from "../components/ui/button"
import { Card } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Textarea } from "../components/ui/textarea"
import { cancelScheduled, getScheduled, scheduleMessage } from "../services/api"
import { useInstanceStore } from "../stores/instanceStore"

export function ScheduledPage() {
  const queryClient = useQueryClient()
  const { selectedInstance } = useInstanceStore()
  const [recipients, setRecipients] = useState("")
  const [text, setText] = useState("")
  const [scheduledAt, setScheduledAt] = useState("")

  const listQuery = useQuery({
    queryKey: ["scheduled", selectedInstance],
    queryFn: () => getScheduled(selectedInstance as string),
    enabled: Boolean(selectedInstance),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      scheduleMessage(
        selectedInstance as string,
        recipients
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        text,
        new Date(scheduledAt).toISOString(),
      ),
    onSuccess: () => {
      toast.success("Mensagem agendada com sucesso.")
      queryClient.invalidateQueries({ queryKey: ["scheduled", selectedInstance] })
    },
    onError: () => toast.error("Falha ao agendar mensagem."),
  })

  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelScheduled(id),
    onSuccess: () => {
      toast.success("Agendamento cancelado.")
      queryClient.invalidateQueries({ queryKey: ["scheduled", selectedInstance] })
    },
  })

  const parsedRecipients = useMemo(() => {
    return recipients
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
  }, [recipients])

  if (!selectedInstance) {
    return <p className="text-sm text-muted">Selecione uma instancia no dashboard primeiro.</p>
  }

  return (
    <div className="grid gap-4 md:grid-cols-[420px_1fr]">
      <Card>
        <h3 className="font-display text-lg">Novo agendamento</h3>
        <p className="mt-1 text-sm text-muted">Informe numeros separados por virgula.</p>
        <div className="mt-3 space-y-3">
          <Input
            placeholder="5511999999999, 5511888888888"
            value={recipients}
            onChange={(event) => setRecipients(event.target.value)}
          />
          <Input type="datetime-local" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} />
          <Textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Mensagem a enviar" />
          <p className="text-xs text-muted">Total de destinatarios: {parsedRecipients.length}</p>
          <Button
            className="w-full"
            disabled={createMutation.isPending || parsedRecipients.length === 0 || !text.trim() || !scheduledAt}
            onClick={() => createMutation.mutate()}
          >
            Agendar envio
          </Button>
        </div>
      </Card>

      <Card>
        <h3 className="font-display text-lg">Agendamentos da instancia</h3>
        <div className="mt-3 space-y-2">
          {(listQuery.data ?? []).map((item) => (
            <div key={item.id} className="rounded-xl border border-border p-3">
              <p className="text-sm text-text">{item.content}</p>
              <p className="text-xs text-muted">
                {new Date(item.scheduled_at).toLocaleString()} | status: {item.status} | enviados: {item.sent_count}
              </p>
              {item.status === "pending" && (
                <Button
                  variant="danger"
                  className="mt-2"
                  onClick={() => cancelMutation.mutate(item.id)}
                  disabled={cancelMutation.isPending}
                >
                  Cancelar
                </Button>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
