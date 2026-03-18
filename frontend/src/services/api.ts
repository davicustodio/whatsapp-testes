import axios from "axios"

import type { Chat, Contact, Instance, Message, SemanticResult } from "../types/domain"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"

const api = axios.create({
  baseURL: API_URL,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("wt_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function login(password: string) {
  const { data } = await api.post<{ access_token: string }>("/auth/login", { password })
  return data
}

export async function getLiveInstances() {
  const { data } = await api.get<Instance[]>("/instances/live")
  return data
}

export async function getLocalInstances() {
  const { data } = await api.get<Instance[]>("/instances")
  return data
}

export async function syncInstance(instanceName: string) {
  const { data } = await api.post(`/instances/${instanceName}/sync`)
  return data
}

export async function getContacts(instanceName: string) {
  const { data } = await api.get<Contact[]>(`/instances/${instanceName}/contacts`)
  return data
}

export async function getChats(instanceName: string) {
  const { data } = await api.get<Chat[]>(`/instances/${instanceName}/chats`)
  return data
}

export async function getMessages(instanceName: string, chatJid: string) {
  const { data } = await api.get<Message[]>(`/instances/${instanceName}/messages`, {
    params: { chat_jid: chatJid },
  })
  return data
}

export async function sendMessage(instanceName: string, number: string, text: string) {
  const { data } = await api.post(`/instances/${instanceName}/messages/send`, {
    number,
    text,
  })
  return data
}

export async function sendBatch(instanceName: string, recipients: string[], text: string) {
  const { data } = await api.post(`/instances/${instanceName}/messages/batch`, {
    recipients,
    text,
  })
  return data
}

export async function scheduleMessage(
  instanceName: string,
  recipients: string[],
  text: string,
  scheduledAt: string,
) {
  const { data } = await api.post(`/instances/${instanceName}/messages/schedule`, {
    recipients,
    text,
    scheduled_at: scheduledAt,
  })
  return data
}

export async function getScheduled(instanceName: string) {
  const { data } = await api.get(`/instances/${instanceName}/messages/scheduled`)
  return data as Array<{
    id: string
    status: string
    scheduled_at: string
    recipients: Array<{ number: string }>
    content: string
    sent_count: number
    failed_count: number
  }>
}

export async function cancelScheduled(id: string) {
  const { data } = await api.delete(`/instances/scheduled/${id}`)
  return data
}

export async function semanticSearch(instanceName: string, query: string, limit = 10) {
  const { data } = await api.post<{ results: SemanticResult[]; rag_answer: string | null }>(
    `/instances/${instanceName}/search`,
    { query, limit },
  )
  return data
}
