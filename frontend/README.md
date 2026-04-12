# TED Bot Frontend

Modern chat interface built with Next.js for talking to the TED Bot agent.

## Quick Start

```bash
pnpm install
pnpm dev
```

Then open http://localhost:3000

## Configuration

Create `.env.local` (or it uses defaults):

```bash
NEXT_PUBLIC_AGENTOS_URL=http://localhost:8000
```

## Features

- 💬 Clean chat interface with message history
- 📊 Workspace panel with interactive table view
- 🛠️ Tool call visualization (see when agent searches)
- 🎨 Dark/light mode support
- 📱 Responsive design

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js pages
│   │   ├── page.tsx           # Main chat page
│   │   └── api/proxy/          # API proxy for backend
│   ├── components/
│   │   ├── chat/              # Chat components
│   │   │   ├── ChatArea/      # Main chat interface
│   │   │   └── Sidebar/       # Sessions and settings
│   │   ├── workspace/         # Workspace table panel
│   │   └── ui/                # Reusable UI components (shadcn/ui)
│   ├── hooks/                 # Custom React hooks
│   │   ├── useAIResponseStream.tsx  # SSE streaming
│   │   └── useChatActions.ts        # Chat operations
│   ├── lib/                   # Utilities
│   └── types/                 # TypeScript types
├── public/                    # Static assets
└── package.json
```

## How It Works

The frontend talks to the backend through the AgentOS API:

1. User sends a message
2. Frontend calls `POST /agents/{id}/runs`
3. Backend streams SSE events back
4. UI updates in real-time with:
   - Agent thinking status
   - Tool calls (when searching TED)
   - Results (markdown or table data)

### Workspace Table

The table panel shows tender results and can be updated by chatting:

- **Creating**: "Find software tenders in Germany" → creates table
- **Filtering**: "Remove all from France" → updates table
- **Adding columns**: "Add deadline dates" → enriches table

See [workspace-panel-spec.md](../docs/workspace-panel-spec.md) for details.

## Development

**Run dev server:**
```bash
pnpm dev
```

**Type checking:**
```bash
pnpm typecheck
```

**Linting:**
```bash
pnpm lint
pnpm format
```

**Build for production:**
```bash
pnpm build
pnpm start
```

## Key Dependencies

- `next` - React framework
- `@radix-ui` - UI primitives
- `tailwindcss` - Styling
- `framer-motion` - Animations
- `nuqs` - URL state management
- `dayjs` - Date formatting

## Customization

- **Themes**: Edit `src/app/globals.css` for colors
- **Components**: All UI components are in `src/components/ui/`
- **API routes**: Modify `src/api/routes.ts` to change backend URL

2. Check the endpoint in the UI sidebar - it should show `http://localhost:8000`

3. Check browser console for CORS errors - the backend should allow `http://localhost:3000`

### Session Not Persisting

Sessions are currently stored in-memory on the backend. They will be lost when the backend restarts.

To add persistence, you could:
- Store sessions in Supabase
- Use Redis for session storage
- Implement file-based storage

## Production Deployment

When deploying to production:

1. **Update environment variables**:
   ```bash
   NEXT_PUBLIC_AGENTOS_URL=https://your-backend-api.com
   ```

2. **Build the app**:
   ```bash
   pnpm build
   ```

3. **Deploy**:
   - Deploy to Vercel (recommended for Next.js)
   - Or use any Node.js hosting platform

## Original Template

This UI is based on the official [Agno Agent UI](https://github.com/agno-agi/agent-ui) template.

For more details on the template features and customization options, see the [original documentation](https://github.com/agno-agi/agent-ui).
