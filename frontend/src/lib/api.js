/* ============================================================================
 * Copyright (c) 2026 Areej Ahmed. All rights reserved.
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
    // Pydantic returns { detail: [...] } for 422 — surface it readably
    const detail = data?.detail
    let msg
    if (Array.isArray(detail)) {
      msg = detail.map(d => {
        const loc = (d.loc || []).join(' → ')
        return `${loc}: ${d.msg || d.type || 'validation error'}`
      }).join('; ')
    } else if (typeof detail === 'string') {
      msg = detail
    } else if (typeof detail === 'object') {
      msg = JSON.stringify(detail)
    } else {
      msg = res.statusText
    }
    throw new Error(`HTTP ${res.status}: ${msg}`)
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

  parseResume: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE}/parse-resume`, {
      method: 'POST',
      body: formData,
      // No Content-Type header — browser sets it with boundary for multipart
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail = data?.detail || res.statusText
      throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
    }
    return data
  },
}
