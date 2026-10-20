# Cortex frontend

Next.js App Router workspace with React 19, Tailwind CSS, and local shadcn/ui components.

## Development

```bash
pnpm install
pnpm dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL` in `.env.local` to your FastAPI server (defaults to `http://localhost:8000`).

## Pages and conversation URLs

- `/` — a new conversation. Sending the first message creates a session and navigates to its URL.
- `/c/[chatId]` — a specific saved conversation. The URL uses the same session ID sent to the chat API. Sidebar links, refresh, and browser back/forward select the conversation from this route.
- `/library` — the document knowledge base.

`app/(workspace)/layout.tsx` keeps the workspace mounted across these pages. `components/workspace/Workspace.tsx` owns sessions, per-chat drafts, document state, and requests so navigating between conversations does not discard a pending answer. Missing IDs show a recovery screen; they never silently create a replacement chat. A URL identifies a conversation in the existing browser/backend history; it does not grant sharing access.

`components/chat/ChatComposer.tsx` implements the expanding message input, attachment button, Enter/Shift+Enter behavior, character limit, and stop control. Stop cancels the frontend request; server-side processing may already be underway.

## Checks

```bash
pnpm lint
pnpm test
pnpm exec tsc --noEmit
pnpm build
```

The Node test suite checks saved-session restoration, chat URLs, stale history merges, interrupted responses, and deleted-session races. Use a browser to check route navigation, direct reloads, mobile layout, and the composer against a running backend.
