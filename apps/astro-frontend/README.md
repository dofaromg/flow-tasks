# Astro Frontend

This is the Astro frontend application for the FlowAgent GKE Starter project.

## 🚀 Quick Start

### Development

```bash
cd apps/astro-frontend
npm install
npm run dev
```

The application will be available at `http://localhost:4321`

### Building for Production

```bash
npm run build
```

The built application will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 📦 Project Structure

```
apps/astro-frontend/
├── public/              # Static assets
├── src/
│   ├── layouts/        # Layout components
│   │   └── Layout.astro
│   └── pages/          # Page components
│       └── index.astro
├── astro.config.mjs    # Astro configuration
├── package.json
└── tsconfig.json
```

## 🧞 Commands

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

## 🔗 Integration with FlowAgent

This frontend is designed to work with:
- **Particle Language Core**: Integration with the particle logic execution framework
- **Module-A**: Backend service module
- **Orchestrator**: Service coordination layer
- **MongoDB**: Data persistence

## 📚 Learn More

- [Astro Documentation](https://docs.astro.build)
- [Astro Discord](https://astro.build/chat)
- [FlowAgent Documentation](../../README.md)
