# NOVARAai Frontend

Next.js 14 frontend for the NOVARAai AI-Powered Grant Screening Platform.

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **TailwindCSS** - Utility-first styling
- **shadcn/ui** - Beautiful, accessible components
- **Axios** - HTTP client
- **Zustand** - State management
- **Lucide React** - Icons

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- NOVARAai backend services running (http://localhost:8000)

## Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Development

```bash
# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── globals.css   # Global styles
│   ├── components/       # React components
│   │   └── ui/           # shadcn/ui components
│   ├── lib/              # Utility functions
│   │   ├── api.ts        # API client
│   │   └── utils.ts      # Helper functions
│   └── types/            # TypeScript types
│       └── index.ts      # Shared types
├── public/               # Static assets
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── tailwind.config.ts    # Tailwind config
└── next.config.js        # Next.js config
```

## Available Pages

- `/` - Home page with platform overview
- `/applications` - Grant applications list (to be implemented)
- `/applications/new` - Submit new application (to be implemented)
- `/screening` - Screening dashboard (to be implemented)
- `/registry` - Identity registry (to be implemented)
- `/dashboard` - Main dashboard (to be implemented)

## API Integration

The frontend connects to the NOVARAai backend services via the API client in `src/lib/api.ts`. All API calls include JWT authentication tokens automatically.

## Component Library

This project uses shadcn/ui components. To add new components:

```bash
npx shadcn-ui@latest add [component-name]
```

## Styling

The project uses TailwindCSS for styling. Custom theme colors are defined in `tailwind.config.ts` and applied via CSS variables in `src/app/globals.css`.

## TypeScript

Strict TypeScript is enabled. All components and functions should have proper type definitions.

## Performance

- Next.js 14 App Router for optimal performance
- Server-side rendering where applicable
- Code splitting by default
- Image optimization with next/image

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT
