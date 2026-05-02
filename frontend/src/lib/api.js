/* ============================================================================
 * Copyright (c) 2026 [YOUR NAME]. All rights reserved.
 * Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
 * Licensed under the JobPilot Evaluation & Personal-Use License.
 * See LICENSE and NOTICE.md in the repository root.
 * ========================================================================== */

const BASE = '/api'

async function jsonFetch(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok && !data?.state) {
    const detail = data?.detail || res.statusText
    throw new Error(`HTTP ${res.status}: ${detail}`)
  }
  return data
}

export const api = {
  health: () => jsonFetch('/health'),
  archetypes: () => jsonFetch('/archetypes'),

  platforms: ({ workModes, regions }) =>
    jsonFetch('/platforms', {
      method: 'POST',
      body: JSON.stringify({ work_modes: workModes, regions }),
    }),

  score: ({ jobUrl, candidateArchetypes }) =>
    jsonFetch('/score', {
      method: 'POST',
      body: JSON.stringify({
        job_url: jobUrl,
        candidate_archetypes: candidateArchetypes,
      }),
    }),

  apply: ({ jobUrl, applicant, options }) =>
    jsonFetch('/apply', {
      method: 'POST',
      body: JSON.stringify({ job_url: jobUrl, applicant, options }),
    }),

  batch: ({ jobUrls, applicant, options, pauseSeconds = 8 }) =>
    jsonFetch('/batch', {
      method: 'POST',
      body: JSON.stringify({
        job_urls: jobUrls,
        applicant,
        options,
        pause_seconds: pauseSeconds,
      }),
    }),

  trackerDownloadUrl: (batchId) => `${BASE}/tracker/${batchId}`,
}
