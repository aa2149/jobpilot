# JobPilot Frontend

A polished React + Vite + Tailwind UI for driving the JobPilot backend locally.

## Run it

Make sure the backend is running first (`uvicorn jobpilot.api.server:app --port 8000` from the repo root). Then:

```bash
npm install
npm run dev
# open http://localhost:3000
```

The Vite dev server proxies `/api/*` → `http://localhost:8000`, so the frontend speaks to the local FastAPI backend with no CORS or env wiring needed.

## What you can do from here

- Pick up to two archetypes for the candidate profile
- Paste a Greenhouse job URL (or click a sample one)
- Edit the candidate fields and resume content inline
- Hit **Score Fit** to run the Fit Intelligence pipeline against the job
- Hit **Run to Pre-Submit** to spin up the headless agent
  - Toggle **Watch live** to see the Chromium window in real time
  - Toggle **Auto-submit** with caution — by default the agent halts before the final click

## Stack

- **React 18** with hooks
- **Vite** for instant HMR
- **Tailwind CSS** with a custom editorial color palette (warm ink + accent)
- **Framer Motion** for staggered reveals on archetype cards and result panels
- **Lucide** icons
- **Fraunces** display serif + **Geist** sans + **JetBrains Mono** — chosen to look like a serious technical publication, not generic SaaS

## Design intent

The UI is editorial / refined — not playful, not generic-purple-AI. It treats the Stealth Agent like a precision instrument: typography-first, generous whitespace, fine borders, mono labels for technical metadata, and one warm accent (`#D97757`) used sparingly for affordances. The grain texture and `editorial-underline` element are atmospheric details that signal *care* — the same care the engineering shows.
