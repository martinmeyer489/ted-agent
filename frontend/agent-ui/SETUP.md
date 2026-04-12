# Agent UI Setup Guide

This is the modern chat interface for TED Bot, built with the Agno Agent UI template.

## Quick Start

1. **Install dependencies**:
   ```bash
   cd frontend/agent-ui
   pnpm install
   ```

2. **Start the development server**:
   ```bash
   pnpm dev
   ```

3. **Open the app**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Configuration

The UI is already configured to connect to your TED Bot backend at `http://localhost:8000`.

Configuration is in `.env.local`:
```bash
NEXT_PUBLIC_AGENTOS_URL=http://localhost:8000
```

## How It Works

### Backend Integration

The agent-ui connects to your TED Bot backend through the AgentOS API endpoints:

- **GET /agents** - Lists available agents (TED Tender Search Agent)
- **POST /agents/{agent_id}/runs** - Runs the agent with a message
- **GET /sessions** - Lists conversation sessions
- **GET /sessions/{session_id}/runs** - Gets session history
- **DELETE /sessions/{session_id}** - Deletes a session
- **GET /health** - Health check

### Features

✅ **Real-time Chat Interface** - Clean, modern chat UI
✅ **Session Management** - Maintains conversation history
✅ **Tool Call Visualization** - Shows when the agent uses tools like `search_ted_tenders`
✅ **Markdown Support** - Renders formatted responses with tables
✅ **Multi-modal Support** - Ready for images, audio, video if needed
✅ **Responsive Design** - Works on desktop and mobile

## Usage

1. **Start a conversation**: Type a message like "Find software contracts in Germany"

2. **View results**: The agent will use the TED search tool and display results in a formatted table

3. **Continue chatting**: The UI maintains session history, so you can ask follow-up questions

4. **Manage sessions**: 
   - Start new conversations with the "New Chat" button
   - View previous sessions in the sidebar
   - Delete old sessions to clean up

## Development

### Project Structure

```
frontend/agent-ui/
├── src/
│   ├── app/              # Next.js app router pages
│   ├── components/       # React components
│   │   ├── chat/        # Chat interface components
│   │   └── ui/          # Reusable UI components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utilities
│   └── api/             # API routes configuration
├── .env.local           # Environment configuration
└── package.json         # Dependencies
```

### Customization

- **Styling**: Edit `src/app/globals.css` or component-specific Tailwind classes
- **API Endpoints**: Modify `src/api/routes.ts` if you change backend routes
- **Components**: Customize chat components in `src/components/chat/`

## Troubleshooting

### Connection Issues

If the UI can't connect to the backend:

1. Make sure the backend is running:
   ```bash
   cd backend
   poetry run uvicorn app.main:app --reload --port 8000
   ```

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
