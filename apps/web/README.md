# shakaHive Web Application

Next.js 14 (App Router) + TypeScript + plain CSS.

- `/` — public landing page.
- `/dashboard` — grant-call screening workspace: Overview, Grant Calls, Applications (results table and review workspace), Screening, Review (queue, audit trail, legacy single-proposal workspace), Publications, Sources, Report.

The workspace talks to the FastAPI service through `lib/api.ts`; types in `lib/types.ts` mirror the backend models. Set `NEXT_PUBLIC_API_BASE_URL` (for example in `.env.local`) to the API URL. The role picker in the sidebar is a demo identity sent as request headers, not authentication.

```bash
npm install
npm run dev        # development server
npm run lint
npx tsc --noEmit
npm test           # Vitest + Testing Library component tests
npm run build
```

Workflow and API documentation: [../../docs/grant-workflow.md](../../docs/grant-workflow.md).
