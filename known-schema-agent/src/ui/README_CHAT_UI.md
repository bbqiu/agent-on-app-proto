# Agent Chat UI

A React-based chat interface for interacting with OpenAI Response API compatible agents.

## Features

- **Real-time Streaming**: Support for streaming responses via Server-Sent Events
- **Rich Message Types**: Display messages, tool calls, reasoning, and errors
- **Agent Avatars**: Color-coded avatars for different agents and users
- **Configuration Panel**: Configurable endpoint and system prompts
- **Copy & Timestamps**: Copy messages and view timestamps
- **Responsive Design**: Mobile-friendly interface

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open browser**: Navigate to `http://localhost:5173`

## Configuration

- **Default Endpoint**: `http://0.0.0.0:8000`
- **System Prompt**: Configurable via the Config panel
- **Streaming**: Enabled by default

## Backend Compatibility

This UI is designed to work with any backend that implements the OpenAI Response API format:

### Required Endpoints

- `POST /invocations` - Send messages (both streaming and non-streaming)
- `GET /health` - Health check (optional)

### Message Format

```typescript
// Request
{
  "messages": [{"role": "user", "content": "Hello"}],
  "system_prompt": "You are a helpful assistant",
  "stream": true
}

// Response (streaming)
data: {"chunk": {"type": "message", "content": [{"type": "text", "text": "Hello!"}]}}
data: [DONE]
```

## Components

- **ChatContainer**: Main chat interface
- **MessageList**: Displays conversation history
- **ResponseRenderer**: Renders different message types
- **MessageInput**: Text input with send functionality
- **ConfigPanel**: Settings for endpoint and system prompt

## API Integration

The UI uses React Query for state management and custom hooks for streaming:

- `useAgentApi`: For standard request/response
- `useStreamingChat`: For real-time streaming conversations

## Development

The project uses:
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Zod** for schema validation
- **Lucide React** for icons
- **Vite** for build tooling

## Browser Compatibility

- Chrome 89+
- Firefox 87+
- Safari 14+
- Edge 89+

Requires modern browser support for:
- Server-Sent Events
- Clipboard API
- Fetch API with Streaming