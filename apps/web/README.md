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

# Brand assets and fonts

The web shell uses unchanged copies of the founder-approved horizontal logo and
favicon from `assets/brand/source`. Fredoka and Nunito variable fonts are
self-hosted in `app/fonts`, sourced from the Google Fonts repository
(`ofl/fredoka` and `ofl/nunito`) under the SIL Open Font License 1.1; their
license texts are included alongside the fonts. System fallbacks are defined
in the shared brand tokens.
