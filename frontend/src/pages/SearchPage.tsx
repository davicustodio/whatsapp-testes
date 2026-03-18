import { useState } from "react"

import { Button } from "../components/ui/button"
import { Card } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { useSemanticSearch } from "../hooks/useSearch"
import { useInstanceStore } from "../stores/instanceStore"

export function SearchPage() {
  const { selectedInstance } = useInstanceStore()
  const [query, setQuery] = useState("")
  const searchMutation = useSemanticSearch(selectedInstance)

  if (!selectedInstance) {
    return <p className="text-sm text-muted">Selecione uma instancia no dashboard primeiro.</p>
  }

  const result = searchMutation.data

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-display text-xl">Busca semantica (RAG)</h2>
        <p className="text-sm text-muted">Pergunte sobre um assunto e veja as mensagens mais relevantes.</p>
      </div>

      <div className="flex gap-2">
        <Input placeholder="Ex: conversa sobre pagamento do cliente X" value={query} onChange={(e) => setQuery(e.target.value)} />
        <Button onClick={() => searchMutation.mutate({ query })} disabled={searchMutation.isPending || query.trim().length < 2}>
          Buscar
        </Button>
      </div>

      {result?.rag_answer && (
        <Card>
          <p className="text-sm font-semibold text-accent">Resumo RAG</p>
          <p className="mt-2 text-sm text-text">{result.rag_answer}</p>
        </Card>
      )}

      <div className="space-y-2">
        {(result?.results ?? []).map((item) => (
          <Card key={item.message_id}>
            <p className="text-sm text-text">{item.content || "(sem texto)"}</p>
            <p className="mt-1 text-xs text-muted">
              {item.remote_jid} | score {item.score.toFixed(4)} | {new Date(item.timestamp).toLocaleString()}
            </p>
          </Card>
        ))}
      </div>
    </div>
  )
}
