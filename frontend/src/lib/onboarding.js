/* ============================================================================
 * Copyright (c) 2026 Areej Ahmed. All rights reserved.
 * Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
 * ========================================================================== */
/*
 * Onboarding questions.
 *
 * Each question has 2-4 answer options. Each option carries a "weights"
 * dictionary that maps to archetype contributions. After the user
 * answers all questions, we sum the weights and produce a primary +
 * secondary archetype profile.
 *
 * This is the pre-archetype-picker conversational layer that career-ops
 * doesn't have. It removes the friction of asking the user to read
 * eight definitions and pick. They just answer plain questions.
 */

export const ONBOARDING_QUESTIONS = [
  {
    id: 'q_career_stage',
    title: 'Where are you in your career?',
    subtitle: "Don't overthink — pick the one closest to right now.",
    options: [
      {
        label: 'Early career — I want to learn fast',
        weights: { founder_track: 1.0, deep_specialist: 0.2 },
      },
      {
        label: 'Mid-career — I want to grow into a bigger role',
        weights: { corporate_climber: 1.0, deep_specialist: 0.4 },
      },
      {
        label: 'Mid-career — I want predictability and good benefits',
        weights: { stable_provider: 1.0 },
      },
      {
        label: 'Senior — I want technical depth, not management',
        weights: { deep_specialist: 1.0 },
      },
    ],
  },
  {
    id: 'q_company_size',
    title: 'What kind of company sounds right today?',
    subtitle: 'Tomorrow can be different.',
    options: [
      {
        label: 'Small & scrappy — under 200 people',
        weights: { founder_track: 1.0 },
      },
      {
        label: 'Mid-size & growing — 200–5,000',
        weights: { founder_track: 0.4, corporate_climber: 0.4 },
      },
      {
        label: 'Large & established — 5,000+',
        weights: { corporate_climber: 1.0, stable_provider: 0.5 },
      },
    ],
  },
  {
    id: 'q_work_mode',
    title: 'Where do you want to work from?',
    subtitle: 'This routes which platforms we apply on.',
    multi: true, // multi-select OK
    options: [
      { label: 'Onsite', value: 'onsite', weights: {} },
      { label: 'Hybrid', value: 'hybrid', weights: {} },
      { label: 'Remote', value: 'remote', weights: { remote_first: 1.0 } },
      {
        label: 'Freelance / contract',
        value: 'freelance',
        weights: { remote_first: 0.5 },
      },
    ],
  },
  {
    id: 'q_culture_priority',
    title: 'What matters most to you about workplace culture?',
    subtitle: 'You can pick more than one.',
    multi: true,
    options: [
      {
        label: 'Strong female leadership and lived gender equity',
        weights: { women_forward: 1.0 },
      },
      {
        label: 'Real work-life balance and family-friendly benefits',
        weights: { stable_provider: 0.7, women_forward: 0.3 },
      },
      {
        label: 'A mission I genuinely believe in',
        weights: { mission_believer: 1.0 },
      },
      {
        label: 'Travel and international exposure',
        weights: { globe_trotter: 1.0 },
      },
      {
        label: 'Distributed/async — no return-to-office whiplash',
        weights: { remote_first: 1.0 },
      },
    ],
  },
  {
    id: 'q_region',
    title: 'Where are you based, or where do you want to work?',
    subtitle: 'Routes which regional platforms we apply on.',
    multi: true,
    options: [
      { label: 'United Arab Emirates', value: 'AE', weights: {} },
      { label: 'Saudi Arabia', value: 'SA', weights: {} },
      { label: 'United States', value: 'US', weights: {} },
      { label: 'United Kingdom', value: 'GB', weights: {} },
      { label: 'Europe', value: 'EU', weights: {} },
      { label: 'Global / no preference', value: 'global', weights: {} },
    ],
  },
]

/**
 * Compute archetype profile from answers.
 *
 * @param {Object} answers — { question_id: option_index | option_index[] }
 * @returns {Array} sorted [{ name, weight }] with the top 2 archetypes
 */
export function computeArchetypeProfile(answers) {
  const totals = {}

  for (const q of ONBOARDING_QUESTIONS) {
    const ans = answers[q.id]
    if (ans === undefined || ans === null) continue

    const indices = Array.isArray(ans) ? ans : [ans]
    for (const idx of indices) {
      const opt = q.options[idx]
      if (!opt || !opt.weights) continue
      for (const [archetype, w] of Object.entries(opt.weights)) {
        totals[archetype] = (totals[archetype] || 0) + w
      }
    }
  }

  const sorted = Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .filter(([, w]) => w > 0)

  if (sorted.length === 0) return []

  // Take top 2, normalize weights to sum to 1
  const top = sorted.slice(0, 2)
  const sum = top.reduce((a, b) => a + b[1], 0)
  return top.map(([name, w]) => ({ name, weight: +(w / sum).toFixed(2) }))
}

/**
 * Extract work modes and regions from answers.
 */
export function extractWorkModesAndRegions(answers) {
  const workModes = []
  const regions = []

  const wmAns = answers.q_work_mode
  if (wmAns !== undefined) {
    const indices = Array.isArray(wmAns) ? wmAns : [wmAns]
    for (const idx of indices) {
      const opt = ONBOARDING_QUESTIONS.find(q => q.id === 'q_work_mode').options[idx]
      if (opt?.value) workModes.push(opt.value)
    }
  }

  const regAns = answers.q_region
  if (regAns !== undefined) {
    const indices = Array.isArray(regAns) ? regAns : [regAns]
    for (const idx of indices) {
      const opt = ONBOARDING_QUESTIONS.find(q => q.id === 'q_region').options[idx]
      if (opt?.value) regions.push(opt.value)
    }
  }

  return {
    workModes: workModes.length ? workModes : ['onsite', 'hybrid', 'remote'],
    regions: regions.length ? regions : ['global'],
  }
}
