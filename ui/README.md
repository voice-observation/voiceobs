# voiceobs UI

Next.js 14 web UI for voiceobs - Voice AI Observability platform.

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- voiceobs server running on port 8765 (or configure `NEXT_PUBLIC_API_URL`)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Edit .env.local to set your API URL if needed
```

### Development

```bash
# Start development server on port 3000
npm run dev
```

The UI will be available at `http://localhost:3000`.

API requests are automatically proxied to the voiceobs server (default: `http://localhost:8765`).

### Building for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

### Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch
```

## Project Structure

```
ui/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Dashboard homepage
│   ├── conversations/     # Conversations pages
│   └── failures/          # Failures page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   └── layout/           # Layout components (Sidebar, Header)
├── lib/                  # Utilities and API client
│   ├── api.ts           # Type-safe API client
│   └── utils.ts         # Utility functions
└── public/              # Static assets
```

## API Client

The API client (`lib/api.ts`) provides type-safe methods for interacting with the voiceobs server:

- `api.listConversations()` - Get all conversations
- `api.getConversation(id)` - Get conversation details
- `api.listFailures(severity?, type?)` - Get detected failures
- `api.analyzeAll()` - Analyze all spans
- `api.analyzeConversation(id)` - Analyze specific conversation
- `api.healthCheck()` - Check server health

All methods include automatic retry logic for network errors and server errors.

## Configuration

Set the following environment variables in `.env.local`:

- `NEXT_PUBLIC_API_URL` - URL of the voiceobs server (default: `http://localhost:8765`)

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Jest + Testing Library** - Testing
