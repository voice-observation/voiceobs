# voiceobs Documentation Site

This directory contains the Docusaurus documentation website for voiceobs.

## Local Development

### Prerequisites

- Node.js 18+ and npm

### Setup

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build

Generate static content into the `build` directory:

```bash
npm run build
```

This can be served using any static contents hosting service.

### Serve

Serve the built site locally:

```bash
npm run serve
```

## Project Structure

```
docs-site/
├── docs/              # Documentation markdown files
│   ├── getting-started.md
│   ├── installation.md
│   ├── guides/
│   ├── api/
│   ├── advanced/
│   ├── examples/
│   └── integrations/
├── src/
│   └── css/
│       └── custom.css  # Custom styles
├── static/
│   └── img/            # Static images
├── docusaurus.config.ts # Docusaurus configuration
├── sidebars.ts          # Sidebar navigation
└── package.json
```

## Documentation Workflow

1. Edit markdown files in `docs/`
2. Test locally with `npm start`
3. Commit changes to the repository
4. GitHub Actions will automatically build and deploy to GitHub Pages

## Configuration

- `docusaurus.config.ts` - Main configuration file
- `sidebars.ts` - Sidebar navigation structure

## Deployment

The documentation is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` branch.

See `.github/workflows/docs.yml` for the deployment workflow.

## Adding New Documentation

1. Create a new markdown file in the appropriate `docs/` subdirectory
2. Add the file to `sidebars.ts` to include it in navigation
3. Follow the existing documentation style and format

## Resources

- [Docusaurus Documentation](https://docusaurus.io/docs)
- [Markdown Guide](https://docusaurus.io/docs/markdown-features)
