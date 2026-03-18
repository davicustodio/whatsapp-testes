import { useMutation } from "@tanstack/react-query"
import { KeyRound } from "lucide-react"
import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { toast } from "sonner"

import { Button } from "../components/ui/button"
import { Card } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { login } from "../services/api"
import { useAuthStore } from "../stores/authStore"

export function LoginPage() {
  const navigate = useNavigate()
  const { token, setToken } = useAuthStore()
  const [password, setPassword] = useState("")

  const mutation = useMutation({
    mutationFn: () => login(password),
    onSuccess: (data) => {
      setToken(data.access_token)
      toast.success("Autenticado com sucesso.")
      navigate("/dashboard")
    },
    onError: () => toast.error("Senha invalida."),
  })

  if (token) return <Navigate to="/dashboard" />

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md p-8">
        <h1 className="font-display text-2xl text-text">Acesso protegido</h1>
        <p className="mt-2 text-sm text-muted">
          Informe a senha definida no <code className="rounded bg-[#182247] px-1">AUTH_PASSWORD</code>.
        </p>
        <form
          className="mt-6 space-y-3"
          onSubmit={(event) => {
            event.preventDefault()
            mutation.mutate()
          }}
        >
          <label className="text-sm text-muted">Senha</label>
          <Input
            type="password"
            placeholder="Sua senha"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          <Button className="w-full" disabled={mutation.isPending}>
            <KeyRound className="mr-2 h-4 w-4" />
            Entrar
          </Button>
        </form>
      </Card>
    </div>
  )
}
