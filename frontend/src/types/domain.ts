export type Instance = {
  id?: string
  instance_name: string
  phone_number?: string | null
  profile_name?: string | null
  status?: string | null
  provider?: string
  synced_at?: string | null
}

export type Contact = {
  id: string
  remote_jid: string
  push_name?: string | null
  phone_number?: string | null
  is_business: boolean
}

export type Chat = {
  id: string
  remote_jid: string
  chat_name?: string | null
  is_group: boolean
  unread_count: number
  last_message_at?: string | null
}

export type Message = {
  id: string
  message_external_id: string
  remote_jid: string
  from_me: boolean
  sender_name?: string | null
  content?: string | null
  message_type: string
  timestamp: string
}

export type SemanticResult = {
  message_id: string
  remote_jid: string
  content?: string | null
  timestamp: string
  score: number
}
