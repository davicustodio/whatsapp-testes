import { Search } from "lucide-react"
import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"

import { Badge } from "../components/ui/badge"
import { Card } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { useContacts } from "../hooks/useContacts"
import { useInstanceStore } from "../stores/instanceStore"

export function ContactsPage() {
  const navigate = useNavigate()
  const { selectedInstance } = useInstanceStore()
  const [query, setQuery] = useState("")

  const contactsQuery = useContacts(selectedInstance)

  const contacts = useMemo(() => {
    const rows = contactsQuery.data ?? []
    const normalizedQuery = query.toLowerCase().trim()
    if (!normalizedQuery) return rows
    return rows.filter((contact) => {
      const name = (contact.push_name ?? "").toLowerCase()
      const phone = (contact.phone_number ?? "").toLowerCase()
      const jid = contact.remote_jid.toLowerCase()
      return name.includes(normalizedQuery) || phone.includes(normalizedQuery) || jid.includes(normalizedQuery)
    })
  }, [contactsQuery.data, query])

  if (!selectedInstance) {
    return <p className="text-sm text-muted">Selecione uma instancia no dashboard primeiro.</p>
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="font-display text-xl">Contatos</h2>
          <p className="text-sm text-muted">Instancia ativa: {selectedInstance}</p>
        </div>
        <div className="relative w-full md:max-w-sm">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted" />
          <Input className="pl-9" placeholder="Buscar por nome, numero ou JID" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {contacts.map((contact) => (
          <button
            key={contact.id}
            className="text-left"
            onClick={() => navigate(`/chat?jid=${encodeURIComponent(contact.remote_jid)}`)}
          >
            <Card className="transition hover:border-accent">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="font-medium text-text">{contact.push_name || "Sem nome"}</p>
                  <p className="text-xs text-muted">{contact.phone_number || contact.remote_jid}</p>
                </div>
                {contact.is_business && <Badge>business</Badge>}
              </div>
            </Card>
          </button>
        ))}
      </div>
    </div>
  )
}
