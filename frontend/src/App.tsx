import { Navigate, Route, Routes } from "react-router-dom"

import { AppShell } from "./components/layout/app-shell"
import { useAuthStore } from "./stores/authStore"
import { BatchSendPage } from "./pages/BatchSendPage"
import { ChatPage } from "./pages/ChatPage"
import { ContactsPage } from "./pages/ContactsPage"
import { DashboardPage } from "./pages/DashboardPage"
import { LoginPage } from "./pages/LoginPage"
import { ScheduledPage } from "./pages/ScheduledPage"
import { SearchPage } from "./pages/SearchPage"

function ProtectedRoute() {
  const { token } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  return <AppShell />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="contacts" element={<ContactsPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="batch" element={<BatchSendPage />} />
        <Route path="scheduled" element={<ScheduledPage />} />
        <Route path="search" element={<SearchPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
