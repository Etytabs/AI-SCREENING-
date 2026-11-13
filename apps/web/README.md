# shakaHive Web Application

Next.js 15.5.29 (App Router) + TypeScript + plain CSS.

- `/` — public landing page.
- `/login` — unified Applicant / Grant Administrator demonstration login.
- `/applicant/dashboard` — authenticated Applicant workspace placeholder; submission workflows are planned for later phases.
- `/dashboard` — grant-call screening workspace: Overview, Grant Calls, Applications (results table and review workspace), Screening, Review (queue, audit trail, legacy single-proposal workspace), Publications, Sources, Report.

The workspace talks to the FastAPI service through `lib/api.ts`; types in `lib/types.ts` mirror the backend models. Set `NEXT_PUBLIC_API_BASE_URL` (for example in `.env.local`) to the API URL. After login, the server-issued 15-minute bearer token is held in React memory and is never stored in browser storage. The API derives identity and permissions from that token, not request-supplied role headers.

Enable the synthetic demo authentication locally by setting `AI_SCREENING_DEMO_AUTH_ENABLED=true` and `AI_SCREENING_ENVIRONMENT=development` for the API process. Demo authentication is disabled by default and the API refuses to start if it is enabled with `AI_SCREENING_ENVIRONMENT=production`. The fixed demo credentials are listed in FPDR-002 and displayed on the login page; do not use them with production systems or real data.

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

The web shell uses an unchanged copy of the founder-approved
`assets/brand/source/logo-on-dark.png` in dark headers, plus the supplied
favicon from `assets/brand/source`. Fredoka and Nunito variable fonts are
self-hosted in `app/fonts`, sourced from the Google Fonts repository
(`ofl/fredoka` and `ofl/nunito`) under the SIL Open Font License 1.1; their
license texts are included alongside the fonts. System fallbacks are defined
in the shared brand tokens.
