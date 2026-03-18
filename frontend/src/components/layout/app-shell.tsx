import { MessageCircleMore, Rows2, Search, Send, Timer } from "lucide-react"
import { NavLink, Outlet } from "react-router-dom"

import { useAuthStore } from "../../stores/authStore"
import { useInstanceStore } from "../../stores/instanceStore"
import { Button } from "../ui/button"

const links = [
  { to: "/dashboard", label: "Dashboard", icon: Rows2 },
  { to: "/contacts", label: "Contatos", icon: MessageCircleMore },
  { to: "/chat", label: "Chat", icon: MessageCircleMore },
  { to: "/batch", label: "Envio em lote", icon: Send },
  { to: "/scheduled", label: "Agendamentos", icon: Timer },
  { to: "/search", label: "Busca semantica", icon: Search },
]

export function AppShell() {
  const { logout } = useAuthStore()
  const { selectedInstance } = useInstanceStore()

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-border bg-[#0a1020]/90 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4">
          <div>
            <p className="font-display text-lg text-text">WhatsApp Testes</p>
            <p className="text-xs text-muted">
              Instancia ativa: <span className="text-accent">{selectedInstance ?? "nenhuma"}</span>
            </p>
          </div>
          <Button variant="secondary" onClick={logout}>
            Sair
          </Button>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-7xl grid-cols-1 gap-4 px-4 py-4 md:grid-cols-[250px_1fr]">
        <aside className="rounded-2xl border border-border bg-panel/70 p-3">
          <nav className="flex flex-col gap-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition ${
                    isActive ? "bg-accentSoft text-accent" : "text-muted hover:bg-[#141c36] hover:text-text"
                  }`
                }
              >
                <link.icon size={16} />
                {link.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <section className="rounded-2xl border border-border bg-panel/60 p-4">
          <Outlet />
        </section>
      </main>
    </div>
  )
}
