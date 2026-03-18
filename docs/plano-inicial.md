# Plano de Implementacao - WhatsApp Testes

## Visao Geral da Arquitetura

```mermaid
graph TB
    subgraph frontend [Frontend - React]
        UI["React + Vite\nZustand + TanStack Query\nshadcn/ui + Tailwind"]
    end
    
    subgraph backend [Backend - FastAPI]
        API["FastAPI"]
        ProviderLayer["Provider Abstraction"]
        EmbeddingService["Embedding Service\nsentence-transformers"]
        RAGService["RAG Service"]
        Scheduler["APScheduler"]
    end
    
    subgraph providers [WhatsApp Providers]
        Evolution["Evolution API\nv2.2.3"]
        Meta["Meta Cloud API\n(futuro)"]
    end
    
    subgraph storage [Armazenamento]
        PG["PostgreSQL\n+ pgvector"]
    end
    
    subgraph external [Servicos Externos]
        OpenRouter["OpenRouter\nqwen/qwen3-coder-next"]
    end
    
    UI -->|"REST API"| API
    API --> ProviderLayer
    ProviderLayer -->|".env switch"| Evolution
    ProviderLayer -->|".env switch"| Meta
    API --> EmbeddingService
    API --> RAGService
    API --> Scheduler
    RAGService --> OpenRouter
    EmbeddingService --> PG
    API --> PG
    Evolution -->|"Webhooks"| API
```

## Ambiente Dokploy Existente

- **Projeto "Database"**: PostgreSQL em producao (postgresId: `7jm2xGsfPLbdqyPklr7Vh`)
- **Projeto "Whatsapp-Telegram"**: Evolution API v2.2.3 (composeId: `1DiHEIr6Y7Up5fKkY8YF8`) em `https://evolutionapi-joaocat.duckdns.org`
- **API Key da Evolution API**: Extrair do ambiente Dokploy/manager da Evolution API
- **Novo projeto a criar**: "WhatsApp-Testes" com 2 applications (UI + API)

## Estrutura do Projeto

```
whatsapp-testes/
├── frontend/                    # React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components
│   │   │   ├── layout/          # Shell, Sidebar, Header
│   │   │   ├── contacts/        # ContactList, ContactCard
│   │   │   ├── chat/            # ChatView, MessageBubble, SendBox
│   │   │   ├── batch/           # BatchSelector, BatchCompose
│   │   │   ├── scheduled/       # ScheduleForm, ScheduleList
│   │   │   └── search/          # SearchBar, SearchResults
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── ContactsPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   ├── BatchSendPage.tsx
│   │   │   ├── ScheduledPage.tsx
│   │   │   └── SearchPage.tsx
│   │   ├── stores/              # Zustand stores
│   │   │   ├── authStore.ts
│   │   │   ├── instanceStore.ts
│   │   │   └── chatStore.ts
│   │   ├── hooks/               # TanStack Query hooks
│   │   │   ├── useInstances.ts
│   │   │   ├── useContacts.ts
│   │   │   ├── useChats.ts
│   │   │   ├── useMessages.ts
│   │   │   └── useSearch.ts
│   │   ├── services/            # API client (axios)
│   │   │   └── api.ts
│   │   ├── types/
│   │   └── lib/utils.ts
│   ├── Dockerfile
│   ├── nginx.conf               # Serve SPA + proxy API
│   ├── package.json
│   └── vite.config.ts
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── instances.py
│   │   │   │   ├── contacts.py
│   │   │   │   ├── chats.py
│   │   │   │   ├── messages.py
│   │   │   │   ├── batch.py
│   │   │   │   ├── scheduled.py
│   │   │   │   └── search.py
│   │   │   └── deps.py          # Auth dependency, DB session
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings (.env)
│   │   │   └── security.py      # Password/token validation
│   │   ├── db/
│   │   │   ├── base.py          # SQLAlchemy Base
│   │   │   ├── session.py       # Engine + SessionLocal
│   │   │   └── models/
│   │   │       ├── instance.py
│   │   │       ├── contact.py
│   │   │       ├── chat.py
│   │   │       ├── message.py
│   │   │       ├── scheduled_message.py
│   │   │       └── batch_message.py
│   │   ├── providers/           # Abstraction Layer
│   │   │   ├── base.py          # WhatsAppProvider (ABC)
│   │   │   ├── evolution.py     # EvolutionProvider
│   │   │   ├── meta.py          # MetaCloudProvider (stub)
│   │   │   └── factory.py       # get_provider() via .env
│   │   ├── services/
│   │   │   ├── sync_service.py      # Sync contatos/chats/mensagens
│   │   │   ├── message_service.py   # Envio de mensagens
│   │   │   ├── embedding_service.py # Gerar embeddings
│   │   │   ├── search_service.py    # RAG + busca semantica
│   │   │   ├── scheduler_service.py # Mensagens agendadas
│   │   │   └── llm_service.py       # OpenRouter integration
│   │   ├── schemas/             # Pydantic request/response
│   │   └── main.py              # FastAPI app + startup
│   ├── alembic/                 # Migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
├── docker-compose.yml           # Dev: PostgreSQL + pgvector
├── docker-compose.prod.yml      # Prod: UI + API (DB externo)
├── docs/
│   └── plano-inicial.md
├── .env.example
└── README.md
```

## Schema do Banco de Dados

Nome do banco: **whatsapp_testes**

### Tabela `instances`

- `id` UUID PK
- `instance_name` VARCHAR NOT NULL UNIQUE
- `instance_id` VARCHAR (ID original da Evolution/Meta)
- `owner_jid` VARCHAR (ex: 5531999998888@s.whatsapp.net)
- `phone_number` VARCHAR (extraido do JID)
- `profile_name` VARCHAR
- `profile_pic_url` TEXT
- `status` VARCHAR (open, close, created)
- `provider` VARCHAR DEFAULT 'evolution' (evolution / meta)
- `synced_at` TIMESTAMP
- `created_at`, `updated_at` TIMESTAMP

### Tabela `contacts`

- `id` UUID PK
- `instance_id` UUID FK -> instances ON DELETE CASCADE
- `remote_jid` VARCHAR NOT NULL
- `push_name` VARCHAR
- `phone_number` VARCHAR
- `profile_pic_url` TEXT
- `is_business` BOOLEAN DEFAULT FALSE
- `synced_at` TIMESTAMP
- `created_at` TIMESTAMP
- UNIQUE(instance_id, remote_jid)

### Tabela `chats`

- `id` UUID PK
- `instance_id` UUID FK -> instances ON DELETE CASCADE
- `remote_jid` VARCHAR NOT NULL
- `chat_name` VARCHAR
- `last_message_at` TIMESTAMP
- `unread_count` INTEGER DEFAULT 0
- `is_group` BOOLEAN DEFAULT FALSE
- `synced_at` TIMESTAMP
- `created_at` TIMESTAMP
- UNIQUE(instance_id, remote_jid)

### Tabela `messages`

- `id` UUID PK
- `instance_id` UUID FK -> instances
- `chat_id` UUID FK -> chats
- `message_id` VARCHAR (ID original do WhatsApp)
- `remote_jid` VARCHAR NOT NULL
- `from_me` BOOLEAN DEFAULT FALSE
- `sender_jid` VARCHAR
- `sender_name` VARCHAR
- `content` TEXT
- `message_type` VARCHAR DEFAULT 'text' (text, image, video, audio, document, sticker, location, contact)
- `media_url` TEXT
- `media_mimetype` VARCHAR
- `timestamp` TIMESTAMP NOT NULL
- `embedding` vector(384) -- pgvector
- `embedded_at` TIMESTAMP
- `created_at` TIMESTAMP
- UNIQUE(instance_id, message_id)
- INDEX USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)

### Tabela `scheduled_messages`

- `id` UUID PK
- `instance_id` UUID FK -> instances
- `recipients` JSONB NOT NULL (array de {jid, phone, name})
- `content` TEXT NOT NULL
- `message_type` VARCHAR DEFAULT 'text'
- `scheduled_at` TIMESTAMP NOT NULL
- `status` VARCHAR DEFAULT 'pending' (pending, processing, completed, failed, cancelled)
- `sent_count` INTEGER DEFAULT 0
- `failed_count` INTEGER DEFAULT 0
- `error_log` JSONB
- `created_at`, `updated_at` TIMESTAMP

### Tabela `batch_messages`

- `id` UUID PK
- `instance_id` UUID FK -> instances
- `recipients` JSONB NOT NULL
- `content` TEXT NOT NULL
- `message_type` VARCHAR DEFAULT 'text'
- `status` VARCHAR DEFAULT 'pending'
- `total_count`, `sent_count`, `failed_count` INTEGER
- `created_at`, `completed_at` TIMESTAMP

## Provider Pattern (Alternancia Evolution / Meta)

```python
# providers/base.py
class WhatsAppProvider(ABC):
    @abstractmethod
    async def list_instances(self) -> list[InstanceData]: ...
    
    @abstractmethod
    async def get_contacts(self, instance: str) -> list[ContactData]: ...
    
    @abstractmethod
    async def get_chats(self, instance: str) -> list[ChatData]: ...
    
    @abstractmethod
    async def get_messages(self, instance: str, chat_jid: str) -> list[MessageData]: ...
    
    @abstractmethod
    async def send_text(self, instance: str, number: str, text: str) -> dict: ...
    
    @abstractmethod
    async def send_media(self, instance: str, number: str, media_url: str, ...) -> dict: ...

# providers/factory.py
def get_provider() -> WhatsAppProvider:
    if settings.WHATSAPP_PROVIDER == "evolution":
        return EvolutionProvider(settings.EVOLUTION_API_URL, settings.EVOLUTION_API_KEY)
    elif settings.WHATSAPP_PROVIDER == "meta":
        return MetaCloudProvider(settings.META_ACCESS_TOKEN, ...)
```

A alternancia ocorre via variavel `WHATSAPP_PROVIDER` no `.env`. O `MetaCloudProvider` sera implementado como stub na fase inicial, com os metodos levantando `NotImplementedError` e a estrutura pronta para preenchimento futuro.

## Pipeline de Busca Semantica (RAG)

```mermaid
flowchart LR
    subgraph sync [Sincronizacao]
        A["Mensagens do\nWhatsApp"] --> B["Armazena\nno PostgreSQL"]
        B --> C["Gera Embeddings\nall-MiniLM-L6-v2"]
        C --> D["Salva vector(384)\nna coluna embedding"]
    end
    
    subgraph search [Busca RAG]
        E["Pergunta\ndo usuario"] --> F["Embedding\nda pergunta"]
        F --> G["pgvector\ncosine similarity\nTOP 10"]
        G --> H["Contexto +\nPergunta"]
        H --> I["OpenRouter LLM\nqwen3-coder-next"]
        I --> J["Resposta\ncontextualizada"]
    end
```

- **Modelo de embedding**: `sentence-transformers/all-MiniLM-L6-v2` (384 dims, ~80MB)
- **Armazenamento**: Coluna `embedding vector(384)` na tabela messages com indice IVFFlat
- **Sincronizacao inicial**: Ao clicar "Sincronizar" na UI, todas as mensagens sao buscadas, armazenadas e embeddings gerados em batch
- **Incremental**: Webhooks da Evolution API recebem novas mensagens -> armazena -> gera embedding
- **Busca**: Query embeddada -> busca cosine similarity no pgvector -> top 10 resultados -> LLM contextualiza a resposta

## Variaveis de Ambiente (.env)

```
# Autenticacao da UI
AUTH_PASSWORD=<senha-definida-pelo-usuario>
JWT_SECRET_KEY=<chave-secreta-gerada>

# Banco de Dados
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_testes

# Provider WhatsApp (evolution | meta)
WHATSAPP_PROVIDER=evolution

# Evolution API
EVOLUTION_API_URL=https://evolutionapi-joaocat.duckdns.org
EVOLUTION_API_KEY=<extrair-do-dokploy>

# Meta WhatsApp Business (futuro)
META_PHONE_NUMBER_ID=
META_ACCESS_TOKEN=
META_BUSINESS_ACCOUNT_ID=
META_WEBHOOK_VERIFY_TOKEN=

# OpenRouter
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=qwen/qwen3-coder-next

# Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# CORS
CORS_ORIGINS=["http://localhost:5173","https://whatsapp-ui-joaocat.duckdns.org"]
```

## Paginas da Interface UI

### 1. Login

- Campo de senha + botao entrar
- Valida contra `AUTH_PASSWORD` via API, retorna JWT token
- Design limpo e minimalista

### 2. Dashboard (selecao de instancia)

- Lista instancias/numeros WhatsApp disponiveis
- Card por instancia: nome, numero, status (online/offline), ultima sincronizacao
- Botao "Sincronizar" por instancia: dispara extracao de contatos, chats e mensagens + geracao de embeddings
- Indicador de progresso da sincronizacao

### 3. Contatos

- Lista de contatos da instancia selecionada com busca/filtro
- Cada contato: avatar, nome, numero
- Clicar em contato abre o Chat

### 4. Chat (conversa)

- Timeline de mensagens estilo WhatsApp
- Mensagens enviadas/recebidas com bolhas, timestamps
- Campo de envio de mensagem na parte inferior
- Possibilidade de enviar para numero aberto (nao precisa estar nos contatos)

### 5. Envio em Lote

- Seletor de contatos (checkbox + busca)
- Campo de composicao da mensagem
- Botao enviar para todos os selecionados
- Progresso/status do envio em lote

### 6. Mensagens Agendadas

- Formulario: selecionar destinatarios, compor mensagem, definir data/hora
- Lista de agendamentos com status (pendente, enviado, falhou, cancelado)
- Opcao de cancelar agendamentos pendentes

### 7. Busca Semantica (RAG)

- Campo de busca por assunto/topico (linguagem natural)
- Resultados: top 10 mensagens relevantes com contexto (contato, data, chat)
- Resumo gerado pelo LLM contextualizando os achados
- Links para abrir o chat da mensagem encontrada

## Deploy no Dokploy

### Acoes no Dokploy via MCP:

1. **Criar projeto** "WhatsApp-Testes" (`project-create`)
2. **Criar environment** "production" (`environment-create`)
3. **Criar application** "whatsapp-testes-api" (`application-create`)
4. **Criar application** "whatsapp-testes-ui" (`application-create`)
5. **Configurar Git provider** para ambas apps apontando para `https://github.com/davicustodio/whatsapp-testes.git` (`application-saveGitProvider`)
6. **Configurar build type** (`application-saveBuildType`):
   - API: dockerfile, context `./backend`
   - UI: dockerfile, context `./frontend`
7. **Configurar dominios**:
   - UI: `whatsapp-ui-joaocat.duckdns.org` com HTTPS/Let's Encrypt
   - API: `whatsapp-api-joaocat.duckdns.org` com HTTPS/Let's Encrypt
8. **Configurar variaveis de ambiente** para cada app (`application-saveEnvironment`)
9. **Banco de dados producao**: usar o PostgreSQL existente (postgresId: `7jm2xGsfPLbdqyPklr7Vh`), criar database `whatsapp_testes` e habilitar extensao `pgvector`
10. **Deploy** ambas applications (`application-deploy`)

## Tecnologias e Dependencias

### Frontend

- React 19 + Vite
- TypeScript
- Zustand (state management)
- TanStack Query v5 (data fetching + cache)
- shadcn/ui (componentes)
- Tailwind CSS v4
- React Router v7
- Axios (HTTP client)
- date-fns (formatacao de datas)
- Lucide React (icones)

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x (async, com asyncpg)
- Alembic (migrations)
- Pydantic v2 (schemas + settings)
- httpx (HTTP client async para Evolution/Meta API)
- sentence-transformers (embeddings locais)
- pgvector (extensao PostgreSQL + binding Python)
- APScheduler (agendamento de mensagens)
- PyJWT (autenticacao)
- uvicorn (ASGI server)

### Infraestrutura

- Docker + Docker Compose (dev local: PostgreSQL 16 + pgvector)
- Dokploy (deploy producao)
- Nginx (serve frontend SPA)

## Docker Compose Local (Desenvolvimento)

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: whatsapp_testes
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Usa a imagem oficial `pgvector/pgvector:pg16` que ja inclui o PostgreSQL 16 com a extensao pgvector pre-instalada.

## Webhooks (Novas Mensagens Incrementais)

A API tera um endpoint `/webhooks/evolution` que recebera eventos da Evolution API:

- `MESSAGES_UPSERT`: nova mensagem -> armazena no banco + gera embedding
- `CONTACTS_UPSERT`: novos contatos -> atualiza banco
- `CHATS_UPSERT`: novos chats -> atualiza banco

Sera configurado na Evolution API para apontar webhooks para `https://whatsapp-api-joaocat.duckdns.org/webhooks/evolution`.

## Fluxo Principal do Usuario

1. Acessa `whatsapp-ui-joaocat.duckdns.org` -> Login com senha
2. Dashboard mostra instancias disponiveis -> seleciona uma
3. Clica "Sincronizar" -> API busca contatos, chats e mensagens da Evolution API -> armazena no PostgreSQL -> gera embeddings
4. Navega pelos contatos -> abre um chat -> ve mensagens -> envia mensagem
5. Pode enviar para numero aberto digitando o numero
6. Pode selecionar multiplos contatos para envio em lote
7. Pode agendar envio para data/hora futura
8. Pode buscar por assunto nas mensagens via RAG -> recebe top 10 resultados + resumo do LLM

## Fases de Implementacao

### Fase 1: Setup do projeto
- Estrutura de pastas, docker-compose local (pgvector), .env, README, Dockerfiles

### Fase 2: Backend core
- FastAPI skeleton, SQLAlchemy models, Alembic migrations, config, autenticacao JWT

### Fase 3: Provider Pattern
- WhatsAppProvider ABC, EvolutionProvider (completo), MetaCloudProvider (stub), factory

### Fase 4: Sync Service
- Endpoints para listar instancias, sincronizar contatos/chats/mensagens, armazenar no banco

### Fase 5: Messaging
- Envio de mensagens (individual, lote, numero aberto), webhook receiver para mensagens incrementais

### Fase 6: Embeddings + RAG
- sentence-transformers, geracao de embeddings em batch e incremental, busca semantica com pgvector, integracao OpenRouter LLM

### Fase 7: Scheduler
- APScheduler para mensagens agendadas, CRUD de agendamentos

### Fase 8: Frontend base
- React + Vite + shadcn + Tailwind + Zustand + TanStack Query, roteamento, layout, login

### Fase 9: Frontend pages
- Dashboard, Contatos, Chat, Envio em Lote, Agendamento, Busca Semantica

### Fase 10: Deploy Dokploy
- Criar projeto, applications, dominios, configurar Git provider, variaveis de ambiente, pgvector no PostgreSQL producao, deploy
