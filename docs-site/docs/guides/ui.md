# UI Guide

The voiceobs UI provides a web interface for viewing and analyzing voice conversations.

## Overview

The voiceobs UI is a Next.js application that connects to the voiceobs server API to display:
- Conversation timelines
- Turn-by-turn analysis
- Failure detection
- Latency metrics

## Setup

The UI is located in the `ui/` directory of the voiceobs repository.

### Prerequisites

- Node.js 18+ and npm
- voiceobs server running (see [Server Guide](./server.md))

### Installation

```bash
cd ui
npm install
```

### Configuration

Create `.env.local` from `.env.local.example`:

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8765
```

### Development

Start the development server:

```bash
npm run dev
```

The UI will be available at `http://localhost:3000`.

### Production Build

```bash
npm run build
npm start
```

## API Integration

The UI connects to the voiceobs server API. Ensure the server is running and accessible at the configured `NEXT_PUBLIC_API_URL`.

## Deployment

### Docker

Build Docker image:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## Next Steps

- [Server Guide](./server.md)
- [Server API Reference](../api/server-api.md)
