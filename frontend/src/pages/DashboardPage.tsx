import { RefreshCcw, Smartphone } from "lucide-react"
import { toast } from "sonner"

import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Card } from "../components/ui/card"
import { useLiveInstances, useSyncInstance } from "../hooks/useInstances"
import { useInstanceStore } from "../stores/instanceStore"

export function DashboardPage() {
  const { selectedInstance, setSelectedInstance } = useInstanceStore()
  const liveQuery = useLiveInstances(true)
  const syncMutation = useSyncInstance()

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display text-xl">Instancias e sincronizacao</h2>
        <p className="text-sm text-muted">
          Escolha um numero WhatsApp e execute a carga de contatos, chats e mensagens.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {(liveQuery.data ?? []).map((instance) => {
          const isActive = selectedInstance === instance.instance_name
          return (
            <Card key={instance.instance_name} className={isActive ? "border-accent" : ""}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-text">{instance.profile_name || instance.instance_name}</p>
                  <p className="text-xs text-muted">{instance.phone_number || "sem numero"}</p>
                </div>
                <Badge variant={instance.status === "open" ? "success" : "warning"}>
                  {instance.status || "desconhecido"}
                </Badge>
              </div>
              <div className="mt-4 flex gap-2">
                <Button
                  variant={isActive ? "primary" : "secondary"}
                  onClick={() => setSelectedInstance(instance.instance_name)}
                  className="flex-1"
                >
                  <Smartphone className="mr-2 h-4 w-4" />
                  {isActive ? "Selecionada" : "Selecionar"}
                </Button>
                <Button
                  variant="ghost"
                  onClick={async () => {
                    try {
                      const data = await syncMutation.mutateAsync(instance.instance_name)
                      toast.success(
                        `Sync concluido: ${data.contacts_count} contatos, ${data.chats_count} chats, ${data.embedded_count} embeddings.`,
                      )
                    } catch {
                      toast.error("Falha ao sincronizar a instancia.")
                    }
                  }}
                  disabled={syncMutation.isPending}
                >
                  <RefreshCcw className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
