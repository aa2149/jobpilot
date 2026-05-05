/* ============================================================================
 * Copyright (c) 2026 Areej Ahmed. All rights reserved.
 * Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
 * Licensed under the JobPilot Evaluation & Personal-Use License.
 * See LICENSE and NOTICE.md in the repository root.
 * ========================================================================== */

import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowRight, ArrowLeft, Sparkles, Shield, Send,
  CheckCircle2, XCircle, Loader2, Eye, EyeOff,
  Compass, FileText, Download, Mail, Activity,
} from 'lucide-react'
import { api } from './lib/api'
import {
  ONBOARDING_QUESTIONS,
  computeArchetypeProfile,
  extractWorkModesAndRegions,
} from './lib/onboarding'

const SAMPLE_JOBS = [
  { label: 'Grammarly · Senior PM', url: 'https://job-boards.greenhouse.io/grammarly/jobs/7767680' },
  { label: 'Geotab · Senior PM (Remote)', url: 'https://job-boards.greenhouse.io/geotab/jobs/5041684008' },
  { label: 'Thumbtack · Sr Product Marketing', url: 'https://job-boards.greenhouse.io/thumbtack/jobs/7746391' },
  { label: 'Modern Health · Sr PMM', url: 'https://job-boards.greenhouse.io/modernhealth/jobs/8465250002' },
  { label: 'Marqeta · Product Support Eng', url: 'https://job-boards.greenhouse.io/marqeta/jobs/7724959' },
  { label: 'Shift4 · Sr Manager Product Learning', url: 'https://job-boards.greenhouse.io/shift4/jobs/5092608007' },
  { label: 'Wavelo · Principal Engineer', url: 'https://job-boards.greenhouse.io/wavelo/jobs/7683905003' },
  { label: 'Rocket Lawyer · Tech PM', url: 'https://job-boards.greenhouse.io/rocketlawyer/jobs/5168904008' },
  { label: 'AutoTrader.ca · Product Ops Lead', url: 'https://job-boards.greenhouse.io/autotradercanada/jobs/7681994003' },
  { label: 'AppDirect · Product Marketing', url: 'https://job-boards.greenhouse.io/appdirectraas/jobs/8483919002' },
]

const STEPS = ['welcome', 'onboarding', 'profile', 'review', 'jobs', 'apply', 'results']

// =====================================================================
// UI primitives
// =====================================================================
function Pill({ children, tone = 'default' }) {
  const tones = {
    default: 'bg-ink-100 text-ink-600 border-ink-200',
    accent: 'bg-accent/10 text-accent-deep border-accent/30',
    success: 'bg-emerald-50 text-emerald-ink border-emerald-200',
    warn: 'bg-amber-50 text-amber-900 border-amber-200',
    fail: 'bg-rose-50 text-rose-900 border-rose-200',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium border ${tones[tone]} font-mono tracking-wider uppercase`}>
      {children}
    </span>
  )
}

function SectionLabel({ children, num }) {
  return (
    <div className="flex items-baseline gap-3 mb-2">
      {num && <span className="font-mono text-[11px] text-accent tracking-wider">{num}</span>}
      <span className="font-mono text-[11px] text-ink-400 tracking-[0.25em] uppercase">{children}</span>
    </div>
  )
}

function StepDots({ current, total }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1 rounded-full transition-all ${
            i === current ? 'w-8 bg-accent' : i < current ? 'w-4 bg-ink-400' : 'w-4 bg-ink-200'
          }`}
        />
      ))}
    </div>
  )
}

function PrimaryButton({ children, onClick, disabled, fullWidth = false }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center justify-center gap-2 px-6 py-3 rounded-md font-medium text-sm transition-all ${
        disabled
          ? 'bg-ink-200 text-ink-400 cursor-not-allowed'
          : 'bg-ink-900 text-ink-50 hover:bg-ink-700'
      } ${fullWidth ? 'w-full' : ''}`}
    >
      {children}
    </button>
  )
}

function SecondaryButton({ children, onClick, disabled, fullWidth = false }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center justify-center gap-2 px-6 py-3 rounded-md font-medium text-sm transition-all border ${
        disabled
          ? 'border-ink-200 text-ink-300 cursor-not-allowed'
          : 'border-ink-300 text-ink-700 hover:bg-ink-100'
      } ${fullWidth ? 'w-full' : ''}`}
    >
      {children}
    </button>
  )
}

function AccentButton({ children, onClick, disabled, fullWidth = false }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center justify-center gap-2 px-6 py-3 rounded-md font-medium text-sm transition-all ${
        disabled
          ? 'bg-ink-200 text-ink-400 cursor-not-allowed'
          : 'bg-accent text-ink-50 hover:bg-accent-deep'
      } ${fullWidth ? 'w-full' : ''}`}
    >
      {children}
    </button>
  )
}

// =====================================================================
// Step Frame — wraps every step with consistent layout
// =====================================================================
function StepFrame({ children, stepIdx, totalSteps, onBack }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 backdrop-blur bg-ink-50/80 border-b border-ink-200/60 px-8 lg:px-16 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="font-display text-xl tracking-tight">JobPilot</div>
            <div className="text-[10px] font-mono text-ink-400 tracking-[0.2em] uppercase">
              © 2026 Areej Ahmed · 1000Jobs Final Stage
            </div>
          </div>
          {onBack && stepIdx > 0 && (
            <button
              onClick={onBack}
              className="text-xs font-mono text-ink-500 hover:text-ink-900 flex items-center gap-1"
            >
              <ArrowLeft className="w-3 h-3" /> Back
            </button>
          )}
        </div>
        <div className="max-w-4xl mx-auto mt-3">
          <StepDots current={stepIdx} total={totalSteps} />
        </div>
      </header>

      <main className="flex-1 px-8 lg:px-16 py-12 lg:py-20 max-w-4xl mx-auto w-full">
        <AnimatePresence mode="wait">
          {children}
        </AnimatePresence>
      </main>

      <footer className="px-8 lg:px-16 py-6 border-t border-ink-200 max-w-4xl mx-auto w-full">
        <div className="text-[10px] font-mono text-ink-400 tracking-wider uppercase">
          © 2026 Areej Ahmed · All rights reserved · See LICENSE & NOTICE.md
        </div>
      </footer>
    </div>
  )
}

function StepWrap({ children, kind = 'div' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35 }}
    >
      {children}
    </motion.div>
  )
}

// =====================================================================
// Step 1: Welcome
// =====================================================================
function StepWelcome({ onStart, healthy }) {
  return (
    <StepWrap>
      <SectionLabel num="01">Welcome</SectionLabel>

      <h1 className="font-display text-5xl lg:text-7xl leading-[0.95] tracking-tight text-ink-900 mt-4">
        Don't apply to{' '}
        <span className="italic font-light">any</span> 1,000 jobs.
      </h1>
      <h1 className="font-display text-5xl lg:text-7xl leading-[0.95] tracking-tight text-ink-900 mt-2">
        Apply to your <span className="editorial-underline">top</span> 1,000.
      </h1>

      <p className="mt-10 max-w-2xl text-lg leading-relaxed text-ink-600">
        JobPilot is an autonomous job-application agent that knows when to <em>not</em> apply.
        Answer five quick questions; we'll figure out the kind of workplace you'd actually thrive at,
        route to the right platforms, and apply on your behalf — sharply and at human speed.
      </p>

      <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-px bg-ink-200 border border-ink-200 rounded-md overflow-hidden">
        <SmallStat label="Bot Mitigation" value="4 Layers" />
        <SmallStat label="Archetypes" value="8" />
        <SmallStat label="Platforms" value="32" />
        <SmallStat label="LLM" value="Gemini" />
      </div>

      <div className="mt-12 flex items-center gap-4">
        <AccentButton onClick={onStart}>
          Get started <ArrowRight className="w-4 h-4" />
        </AccentButton>
        {healthy === null ? (
          <Pill><Loader2 className="w-3 h-3 animate-spin" /> Connecting</Pill>
        ) : healthy ? (
          <Pill tone="success">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-ink animate-pulse-soft" /> API online
          </Pill>
        ) : (
          <Pill tone="fail"><XCircle className="w-3 h-3" /> API offline</Pill>
        )}
      </div>

      <p className="mt-12 text-xs text-ink-400 italic font-display max-w-xl">
        Submitted to the 1000Jobs Final Stage assessment for evaluation only.
        Source-available, not open source. See LICENSE and NOTICE.md.
      </p>
    </StepWrap>
  )
}

function SmallStat({ label, value }) {
  return (
    <div className="bg-ink-50 px-4 py-4">
      <div className="font-mono text-[10px] text-ink-400 tracking-[0.25em] uppercase">{label}</div>
      <div className="font-display text-2xl text-ink-900 mt-1">{value}</div>
    </div>
  )
}

// =====================================================================
// Step 2: Onboarding (Q&A)
// =====================================================================
function StepOnboarding({ answers, setAnswers, qIdx, setQIdx, onComplete }) {
  const q = ONBOARDING_QUESTIONS[qIdx]
  if (!q) return null

  function pickOption(idx) {
    if (q.multi) {
      const cur = answers[q.id] || []
      const arr = Array.isArray(cur) ? cur : [cur]
      const next = arr.includes(idx) ? arr.filter(x => x !== idx) : [...arr, idx]
      setAnswers({ ...answers, [q.id]: next })
    } else {
      setAnswers({ ...answers, [q.id]: idx })
      // Auto-advance after a brief pause for non-multi
      setTimeout(() => {
        if (qIdx < ONBOARDING_QUESTIONS.length - 1) {
          setQIdx(qIdx + 1)
        } else {
          onComplete()
        }
      }, 350)
    }
  }

  function isSelected(idx) {
    const ans = answers[q.id]
    if (ans === undefined) return false
    if (Array.isArray(ans)) return ans.includes(idx)
    return ans === idx
  }

  function handleNext() {
    if (qIdx < ONBOARDING_QUESTIONS.length - 1) {
      setQIdx(qIdx + 1)
    } else {
      onComplete()
    }
  }

  const canAdvance = answers[q.id] !== undefined &&
    (Array.isArray(answers[q.id]) ? answers[q.id].length > 0 : true)

  return (
    <StepWrap>
      <SectionLabel num={`02 · Q${qIdx + 1}/${ONBOARDING_QUESTIONS.length}`}>
        About you
      </SectionLabel>

      <h2 className="font-display text-4xl lg:text-5xl leading-tight text-ink-900 mt-3">
        {q.title}
      </h2>
      <p className="mt-3 text-base text-ink-500 italic font-display">{q.subtitle}</p>

      <div className="mt-10 space-y-3">
        {q.options.map((opt, i) => (
          <motion.button
            key={i}
            onClick={() => pickOption(i)}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04 }}
            className={`w-full text-left p-5 border rounded-md transition-all duration-200 ${
              isSelected(i)
                ? 'border-accent bg-accent/[0.04] shadow-[0_0_0_3px_rgba(217,119,87,0.08)]'
                : 'border-ink-200 hover:border-ink-400 bg-ink-50'
            }`}
          >
            <div className="flex items-center gap-4">
              <div
                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors flex-shrink-0 ${
                  isSelected(i) ? 'border-accent bg-accent' : 'border-ink-300'
                }`}
              >
                {isSelected(i) && <CheckCircle2 className="w-3 h-3 text-white" strokeWidth={3} />}
              </div>
              <span className={`text-base ${isSelected(i) ? 'text-accent-deep font-medium' : 'text-ink-700'}`}>
                {opt.label}
              </span>
            </div>
          </motion.button>
        ))}
      </div>

      {q.multi && (
        <div className="mt-10 flex items-center justify-end gap-3">
          <span className="text-xs font-mono text-ink-400 italic">
            {Array.isArray(answers[q.id]) ? `${answers[q.id].length} selected` : ''}
          </span>
          <PrimaryButton onClick={handleNext} disabled={!canAdvance}>
            Continue <ArrowRight className="w-4 h-4" />
          </PrimaryButton>
        </div>
      )}
    </StepWrap>
  )
}

// =====================================================================
// Step 3: Profile reveal — show computed archetype + work mode
// =====================================================================
function StepProfile({ archetypes, workModes, regions, onContinue }) {
  return (
    <StepWrap>
      <SectionLabel num="03">Your profile</SectionLabel>

      <h2 className="font-display text-4xl lg:text-5xl leading-tight text-ink-900 mt-3">
        Here's who we think you are.
      </h2>
      <p className="mt-3 text-base text-ink-500 italic font-display">
        We'll only apply to companies that look like a real fit for this profile.
      </p>

      <div className="mt-10 space-y-6">
        <div>
          <SectionLabel>Archetype</SectionLabel>
          <div className="mt-3 space-y-2">
            {archetypes.length === 0 ? (
              <div className="text-ink-400 text-sm font-mono">
                Couldn't infer an archetype — your answers were too neutral. Default to Stable Provider.
              </div>
            ) : (
              archetypes.map((a, i) => (
                <div
                  key={a.name}
                  className="flex items-center justify-between p-4 border border-ink-200 rounded-md bg-white"
                >
                  <div>
                    <div className="text-[10px] font-mono text-accent tracking-wider uppercase">
                      {i === 0 ? 'Primary' : 'Secondary'}
                    </div>
                    <div className="font-display text-xl text-ink-900 mt-1 capitalize">
                      {a.name.replace(/_/g, ' ')}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-display text-3xl tabular-nums text-accent">
                      {Math.round(a.weight * 100)}
                      <span className="text-base text-ink-400">%</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div>
          <SectionLabel>Work mode</SectionLabel>
          <div className="mt-3 flex flex-wrap gap-2">
            {workModes.map(m => (
              <span key={m} className="px-3 py-1.5 bg-accent/10 border border-accent/30 text-accent-deep rounded-full text-xs font-mono tracking-wider uppercase">
                {m}
              </span>
            ))}
          </div>
        </div>

        <div>
          <SectionLabel>Region</SectionLabel>
          <div className="mt-3 flex flex-wrap gap-2">
            {regions.map(r => (
              <span key={r} className="px-3 py-1.5 bg-ink-100 border border-ink-200 text-ink-600 rounded-full text-xs font-mono tracking-wider uppercase">
                {r}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-12 flex justify-end">
        <AccentButton onClick={onContinue}>
          Looks right <ArrowRight className="w-4 h-4" />
        </AccentButton>
      </div>
    </StepWrap>
  )
}

// =====================================================================
// Step 4: Review — collect resume + applicant details
// =====================================================================
function StepReview({ applicant, setApplicant, onContinue }) {
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [parsed, setParsed] = useState(false) // true once auto-filled

  const canAdvance = applicant.first_name && applicant.last_name && applicant.email && applicant.resume_path && applicant.resume_text

  async function handleFileUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setUploadError(null)

    try {
      const data = await api.parseResume(file)

      // Auto-fill all fields from parsed data
      setApplicant(prev => ({
        ...prev,
        first_name: data.first_name || prev.first_name,
        last_name: data.last_name || prev.last_name,
        email: data.email || prev.email,
        phone: data.phone || prev.phone,
        location: data.location || prev.location,
        linkedin: data.linkedin || prev.linkedin,
        github: data.github || prev.github,
        portfolio: data.portfolio || prev.portfolio,
        work_auth: data.work_auth || prev.work_auth,
        resume_text: data.resume_text || prev.resume_text,
        resume_path: data.resume_path || prev.resume_path,
      }))
      setParsed(true)
    } catch (err) {
      setUploadError(err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <StepWrap>
      <SectionLabel num="04">Your details</SectionLabel>

      <h2 className="font-display text-4xl lg:text-5xl leading-tight text-ink-900 mt-3">
        Upload your resume — we'll do the rest.
      </h2>
      <p className="mt-3 text-base text-ink-500 italic font-display">
        Drop a PDF and Gemini auto-fills every field. You can edit anything before continuing.
      </p>

      {/* Resume upload zone */}
      <div className="mt-8">
        <label
          className={`relative flex flex-col items-center justify-center p-10 border-2 border-dashed rounded-lg cursor-pointer transition-all ${
            uploading
              ? 'border-accent bg-accent/5'
              : parsed
                ? 'border-emerald-ink/30 bg-emerald-50'
                : 'border-ink-300 hover:border-accent hover:bg-accent/[0.02]'
          }`}
        >
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={uploading}
          />

          {uploading ? (
            <>
              <Loader2 className="w-8 h-8 text-accent animate-spin mb-3" />
              <span className="font-display text-lg text-accent">Parsing your resume with Gemini…</span>
              <span className="text-xs text-ink-500 mt-1 font-mono">Extracting text → identifying fields → auto-filling</span>
            </>
          ) : parsed ? (
            <>
              <CheckCircle2 className="w-8 h-8 text-emerald-ink mb-3" />
              <span className="font-display text-lg text-emerald-ink">Resume parsed — fields auto-filled</span>
              <span className="text-xs text-ink-500 mt-1">
                {applicant.resume_path ? applicant.resume_path.split('/').pop() : 'resume.pdf'}
                {' · '}Drop another PDF to re-parse
              </span>
            </>
          ) : (
            <>
              <FileText className="w-8 h-8 text-ink-400 mb-3" />
              <span className="font-display text-lg text-ink-700">Drop your resume PDF here</span>
              <span className="text-xs text-ink-500 mt-1">or click to browse · PDF only · max 10 MB</span>
            </>
          )}
        </label>

        {uploadError && (
          <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded text-sm">
            <div className="flex items-center gap-2 text-rose-900 font-medium">
              <XCircle className="w-4 h-4" /> Parse failed
            </div>
            <div className="mt-1 text-rose-800 text-xs font-mono">{uploadError}</div>
          </div>
        )}
      </div>

      {/* Auto-filled fields (editable) */}
      <div className="mt-8 space-y-5">
        {parsed && (
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-accent" />
            <span className="text-xs font-mono text-accent tracking-wider uppercase">
              Auto-filled from your resume · edit anything below
            </span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <Field label="First name">
            <input value={applicant.first_name} onChange={(e) => setApplicant({ ...applicant, first_name: e.target.value })} className="form-input" />
          </Field>
          <Field label="Last name">
            <input value={applicant.last_name} onChange={(e) => setApplicant({ ...applicant, last_name: e.target.value })} className="form-input" />
          </Field>
        </div>

        <Field label="Email">
          <input type="email" value={applicant.email} onChange={(e) => setApplicant({ ...applicant, email: e.target.value })} className="form-input" />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Phone">
            <input type="tel" value={applicant.phone} onChange={(e) => setApplicant({ ...applicant, phone: e.target.value })} className="form-input" />
          </Field>
          <Field label="Location">
            <input value={applicant.location} onChange={(e) => setApplicant({ ...applicant, location: e.target.value })} className="form-input" />
          </Field>
        </div>

        <Field label="LinkedIn URL">
          <input type="url" value={applicant.linkedin || ''} onChange={(e) => setApplicant({ ...applicant, linkedin: e.target.value })} className="form-input" />
        </Field>

        <Field label="GitHub URL">
          <input type="url" value={applicant.github || ''} onChange={(e) => setApplicant({ ...applicant, github: e.target.value })} className="form-input" />
        </Field>

        <Field label="Portfolio / website">
          <input type="url" value={applicant.portfolio || ''} onChange={(e) => setApplicant({ ...applicant, portfolio: e.target.value })} className="form-input" />
        </Field>

        {applicant.resume_path && (
          <Field label="Resume PDF path" hint="Saved to your machine — the agent reads this file when uploading to forms.">
            <input type="text" value={applicant.resume_path} readOnly className="form-input font-mono text-xs bg-ink-100 cursor-default" />
          </Field>
        )}

        <Field label="Resume text" hint="What Gemini reads when answering 'Why this company?' questions. Auto-extracted from your PDF.">
          <textarea
            value={applicant.resume_text}
            onChange={(e) => setApplicant({ ...applicant, resume_text: e.target.value })}
            rows={6}
            className="form-input font-mono text-xs leading-relaxed"
          />
        </Field>
      </div>

      <div className="mt-10 flex justify-end">
        <AccentButton onClick={onContinue} disabled={!canAdvance}>
          Continue <ArrowRight className="w-4 h-4" />
        </AccentButton>
      </div>
    </StepWrap>
  )
}

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="font-mono text-[10px] tracking-[0.2em] uppercase text-ink-500">{label}</span>
        {hint && <span className="text-[10px] text-ink-400 italic font-display max-w-md text-right">{hint}</span>}
      </div>
      {children}
    </label>
  )
}

// =====================================================================
// Step 5: Job picker — pick which jobs to apply to
// =====================================================================
function StepJobs({ selectedJobs, setSelectedJobs, customUrl, setCustomUrl, onContinue }) {
  function toggle(url) {
    setSelectedJobs(
      selectedJobs.includes(url)
        ? selectedJobs.filter(u => u !== url)
        : [...selectedJobs, url]
    )
  }

  function addCustom() {
    if (customUrl && !selectedJobs.includes(customUrl)) {
      setSelectedJobs([...selectedJobs, customUrl])
      setCustomUrl('')
    }
  }

  return (
    <StepWrap>
      <SectionLabel num="05">Choose jobs</SectionLabel>

      <h2 className="font-display text-4xl lg:text-5xl leading-tight text-ink-900 mt-3">
        Which jobs should we apply to?
      </h2>
      <p className="mt-3 text-base text-ink-500 italic font-display">
        Pick from the brief's sample list, or paste your own Greenhouse URLs. We'll apply to each in sequence.
      </p>

      <div className="mt-8">
        <div className="flex items-center gap-2 mb-4">
          <SectionLabel>From the brief's sample list</SectionLabel>
          <Pill>{selectedJobs.length} selected</Pill>
        </div>

        <div className="space-y-2">
          {SAMPLE_JOBS.map((j, i) => (
            <button
              key={j.url}
              onClick={() => toggle(j.url)}
              className={`w-full flex items-start gap-3 p-3 border rounded-md text-left transition-all ${
                selectedJobs.includes(j.url)
                  ? 'border-accent bg-accent/[0.04]'
                  : 'border-ink-200 hover:border-ink-400 bg-ink-50'
              }`}
            >
              <div
                className={`mt-0.5 w-4 h-4 rounded-sm border-2 flex items-center justify-center flex-shrink-0 ${
                  selectedJobs.includes(j.url) ? 'border-accent bg-accent' : 'border-ink-300'
                }`}
              >
                {selectedJobs.includes(j.url) && <CheckCircle2 className="w-2.5 h-2.5 text-white" strokeWidth={4} />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-ink-900">{j.label}</div>
                <div className="text-[11px] text-ink-400 font-mono truncate mt-0.5">{j.url}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-8">
        <SectionLabel>Or paste a custom Greenhouse URL</SectionLabel>
        <div className="mt-3 flex gap-2">
          <input
            type="url"
            value={customUrl}
            onChange={(e) => setCustomUrl(e.target.value)}
            placeholder="https://job-boards.greenhouse.io/..."
            className="form-input flex-1 font-mono text-xs"
          />
          <SecondaryButton onClick={addCustom} disabled={!customUrl}>
            Add
          </SecondaryButton>
        </div>
      </div>

      <div className="mt-12 flex items-center justify-between">
        <div className="text-sm text-ink-500">
          {selectedJobs.length === 0 ? (
            <span className="italic">Pick at least one to continue.</span>
          ) : (
            <span>
              <strong>{selectedJobs.length}</strong> jobs queued — estimated ~{Math.ceil(selectedJobs.length * 3)} min
            </span>
          )}
        </div>
        <AccentButton onClick={onContinue} disabled={selectedJobs.length === 0}>
          Apply now <ArrowRight className="w-4 h-4" />
        </AccentButton>
      </div>
    </StepWrap>
  )
}

// =====================================================================
// Step 6: Apply — running batch
// =====================================================================
function StepApply({ jobCount, headless, setHeadless, autoSubmit, setAutoSubmit, onLaunch, applying, applyError }) {
  return (
    <StepWrap>
      <SectionLabel num="06">Final check</SectionLabel>

      <h2 className="font-display text-4xl lg:text-5xl leading-tight text-ink-900 mt-3">
        Ready to apply to {jobCount} jobs?
      </h2>
      <p className="mt-3 text-base text-ink-500 italic font-display">
        This will spin up a stealth browser, fill each form at human speed,
        upload your resume, generate Gemini answers for open-ended questions,
        and submit. ~{Math.ceil(jobCount * 3)} minutes total.
      </p>

      <div className="mt-10 space-y-4">
        <ToggleCard
          icon={headless ? EyeOff : Eye}
          label={headless ? 'Run headless' : 'Watch live in Chromium'}
          sub="See what the agent does in real time. Off = headless, no window. On = Chromium opens; you see it type."
          on={!headless}
          onChange={(v) => setHeadless(!v)}
        />

        <ToggleCard
          icon={Send}
          label={autoSubmit ? 'Submit autonomously' : 'Halt before submit (review mode)'}
          sub="Default is autonomous submit. Review mode stops one click before submit so you can inspect the form."
          on={autoSubmit}
          onChange={setAutoSubmit}
        />
      </div>

      {applyError && (
        <div className="mt-6 p-4 bg-rose-50 border border-rose-200 rounded text-sm">
          <div className="flex items-center gap-2 text-rose-900 font-medium">
            <XCircle className="w-4 h-4" /> Couldn't start the batch
          </div>
          <div className="mt-1 text-rose-800 text-xs font-mono">{applyError}</div>
        </div>
      )}

      <div className="mt-12">
        <AccentButton onClick={onLaunch} disabled={applying} fullWidth>
          {applying ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Agent running…</>
          ) : (
            <>Apply to {jobCount} {jobCount === 1 ? 'job' : 'jobs'} <ArrowRight className="w-4 h-4" /></>
          )}
        </AccentButton>
      </div>

      {applying && (
        <p className="mt-6 text-center text-xs text-ink-500 italic font-display">
          Don't close this tab. Each job takes ~3 minutes. Watch the Chromium window if Live mode is on.
        </p>
      )}
    </StepWrap>
  )
}

function ToggleCard({ icon: Icon, label, sub, on, onChange }) {
  return (
    <button
      onClick={() => onChange(!on)}
      className={`w-full flex items-start gap-4 p-5 border rounded-md text-left transition-all ${
        on ? 'border-accent bg-accent/[0.04]' : 'border-ink-200 hover:border-ink-400 bg-ink-50'
      }`}
    >
      <div className={`p-2 rounded ${on ? 'bg-accent/10 text-accent' : 'bg-ink-100 text-ink-500'}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1">
        <div className={`font-medium ${on ? 'text-accent-deep' : 'text-ink-900'}`}>{label}</div>
        <div className="text-xs text-ink-500 mt-1 leading-relaxed">{sub}</div>
      </div>
      <div className={`w-9 h-5 rounded-full p-0.5 transition-colors flex-shrink-0 ${on ? 'bg-accent' : 'bg-ink-300'}`}>
        <div className={`w-4 h-4 rounded-full bg-white transition-transform ${on ? 'translate-x-4' : ''}`} />
      </div>
    </button>
  )
}

// =====================================================================
// Step 7: Results
// =====================================================================
function StepResults({ batchResult, onRestart }) {
  if (!batchResult) return null

  return (
    <StepWrap>
      <SectionLabel num="07">Results</SectionLabel>

      <h2 className="font-display text-4xl lg:text-5xl leading-tight text-ink-900 mt-3">
        We're done.
      </h2>
      <p className="mt-3 text-base text-ink-500 italic font-display">
        {batchResult.successes > 0
          ? `Applied to ${batchResult.successes} of ${batchResult.total_jobs}. Tracker is ready.`
          : 'Tough run. Some applications didn\'t go through — see the per-job details below.'}
      </p>

      <div className="mt-10 grid grid-cols-3 gap-px bg-ink-200 border border-ink-200 rounded-md overflow-hidden">
        <ResultStat label="Submitted" value={batchResult.successes} tone="success" />
        <ResultStat label="Blocked" value={batchResult.blocked} tone={batchResult.blocked > 0 ? 'fail' : 'default'} />
        <ResultStat label="Failed" value={batchResult.failures} tone={batchResult.failures > 0 ? 'warn' : 'default'} />
      </div>

      {/* Tracker download */}
      <div className="mt-8 p-6 border border-accent/40 bg-accent/5 rounded-md">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-accent/15 rounded">
            <FileText className="w-5 h-5 text-accent-deep" />
          </div>
          <div className="flex-1">
            <div className="font-display text-xl text-ink-900">Your application tracker is ready</div>
            <p className="text-sm text-ink-600 mt-1.5 leading-relaxed">
              One row per company we applied to, with drop-downs for status (Round 1, Round 2, Offer, Rejected, Ghosted)
              and notes. Update it as you hear back to track your funnel.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <a
                href={api.trackerDownloadUrl(batchResult.batch_id)}
                download={`jobpilot_tracker_${batchResult.batch_id}.xlsx`}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-accent text-ink-50 hover:bg-accent-deep text-sm font-medium transition-colors"
              >
                <Download className="w-4 h-4" /> Download tracker.xlsx
              </a>
              {batchResult.email_status === 'stubbed' && batchResult.email_eml_path && (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-ink-200 bg-white text-xs text-ink-600">
                  <Mail className="w-3.5 h-3.5" />
                  <span>
                    Email stubbed → <code className="font-mono text-[11px] text-ink-500">{batchResult.email_eml_path}</code>
                  </span>
                </div>
              )}
            </div>
            {batchResult.email_status === 'stubbed' && (
              <p className="mt-3 text-[11px] text-ink-400 italic font-display">
                In production, this tracker would be emailed to you automatically.
                In v1 we write a real .eml file you can open in any mail client. See REPORT.md §5 for the production-email roadmap.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Per-job table */}
      <div className="mt-8">
        <SectionLabel>Where we applied</SectionLabel>
        <div className="mt-3 border border-ink-200 rounded-md overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-ink-100 text-ink-700">
              <tr>
                <th className="text-left px-4 py-3 font-mono text-[10px] tracking-wider uppercase">Company</th>
                <th className="text-left px-4 py-3 font-mono text-[10px] tracking-wider uppercase">State</th>
                <th className="text-right px-4 py-3 font-mono text-[10px] tracking-wider uppercase">Duration</th>
              </tr>
            </thead>
            <tbody>
              {batchResult.results.map((r, i) => (
                <tr key={i} className={`border-t border-ink-100 ${i % 2 === 1 ? 'bg-ink-50/30' : ''}`}>
                  <td className="px-4 py-3 text-ink-900 font-medium">{r.company || '—'}</td>
                  <td className="px-4 py-3">
                    <StateChip state={r.state} />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-[11px] text-ink-500 tabular-nums">
                    {(r.duration_ms / 1000).toFixed(1)}s
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-12 flex justify-center">
        <SecondaryButton onClick={onRestart}>
          Start over <ArrowRight className="w-4 h-4" />
        </SecondaryButton>
      </div>
    </StepWrap>
  )
}

function ResultStat({ label, value, tone }) {
  const colors = {
    success: 'text-emerald-ink',
    fail: 'text-rose-700',
    warn: 'text-amber-900',
    default: 'text-ink-700',
  }
  return (
    <div className="bg-ink-50 px-6 py-5">
      <div className="font-mono text-[10px] text-ink-400 tracking-[0.25em] uppercase">{label}</div>
      <div className={`font-display text-4xl mt-1 tabular-nums ${colors[tone]}`}>{value}</div>
    </div>
  )
}

function StateChip({ state }) {
  const tone = state === 'submitted' ? 'success'
             : state === 'pre_submit_ready' ? 'accent'
             : state === 'blocked_by_bot_detection' ? 'fail'
             : 'warn'
  return <Pill tone={tone}>{state}</Pill>
}

// =====================================================================
// App — orchestrates the steps
// =====================================================================
const DEFAULT_APPLICANT = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  location: '',
  linkedin: '',
  github: '',
  portfolio: '',
  resume_path: '',
  resume_text: '',
  work_auth: '',
  preferred_pronouns: '',
}

export default function App() {
  const [stepIdx, setStepIdx] = useState(0) // index into STEPS
  const [healthy, setHealthy] = useState(null)

  const [answers, setAnswers] = useState({})
  const [qIdx, setQIdx] = useState(0)

  const [applicant, setApplicant] = useState(DEFAULT_APPLICANT)
  const [selectedJobs, setSelectedJobs] = useState([])
  const [customUrl, setCustomUrl] = useState('')

  const [autoSubmit, setAutoSubmit] = useState(true)
  const [headless, setHeadless] = useState(true)

  const [applying, setApplying] = useState(false)
  const [applyError, setApplyError] = useState(null)
  const [batchResult, setBatchResult] = useState(null)

  const archetypes = useMemo(() => computeArchetypeProfile(answers), [answers])
  const { workModes, regions } = useMemo(() => extractWorkModesAndRegions(answers), [answers])

  useEffect(() => {
    api.health()
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false))
  }, [])

  function go(stepName) {
    setStepIdx(STEPS.indexOf(stepName))
  }

  function back() {
    if (STEPS[stepIdx] === 'onboarding' && qIdx > 0) {
      setQIdx(qIdx - 1)
      return
    }
    if (stepIdx > 0) setStepIdx(stepIdx - 1)
  }

  async function handleLaunch() {
    setApplying(true)
    setApplyError(null)
    try {
      // Clean the applicant: empty strings → null for optional fields
      // so Pydantic doesn't choke on e.g. github="" as an invalid URL
      const cleanApplicant = { ...applicant }
      const optionalFields = ['phone', 'location', 'linkedin', 'github', 'portfolio', 'work_auth', 'preferred_pronouns']
      for (const f of optionalFields) {
        if (!cleanApplicant[f]) cleanApplicant[f] = null
      }

      const result = await api.batch({
        jobUrls: selectedJobs,
        applicant: cleanApplicant,
        options: {
          auto_submit: autoSubmit,
          headless,
          screenshot_on_failure: true,
          min_match_score: 0.0,
        },
        pauseSeconds: 8,
      })
      setBatchResult(result)
      go('results')
    } catch (e) {
      setApplyError(e.message)
    } finally {
      setApplying(false)
    }
  }

  function handleRestart() {
    setStepIdx(0)
    setAnswers({})
    setQIdx(0)
    setSelectedJobs([])
    setBatchResult(null)
  }

  const totalSteps = STEPS.length

  return (
    <div className="bg-grain min-h-screen bg-ink-50">
      <StepFrame stepIdx={stepIdx} totalSteps={totalSteps} onBack={back}>
        {STEPS[stepIdx] === 'welcome' && (
          <StepWelcome onStart={() => go('onboarding')} healthy={healthy} />
        )}
        {STEPS[stepIdx] === 'onboarding' && (
          <StepOnboarding
            answers={answers}
            setAnswers={setAnswers}
            qIdx={qIdx}
            setQIdx={setQIdx}
            onComplete={() => go('profile')}
          />
        )}
        {STEPS[stepIdx] === 'profile' && (
          <StepProfile
            archetypes={archetypes}
            workModes={workModes}
            regions={regions}
            onContinue={() => go('review')}
          />
        )}
        {STEPS[stepIdx] === 'review' && (
          <StepReview
            applicant={applicant}
            setApplicant={setApplicant}
            onContinue={() => go('jobs')}
          />
        )}
        {STEPS[stepIdx] === 'jobs' && (
          <StepJobs
            selectedJobs={selectedJobs}
            setSelectedJobs={setSelectedJobs}
            customUrl={customUrl}
            setCustomUrl={setCustomUrl}
            onContinue={() => go('apply')}
          />
        )}
        {STEPS[stepIdx] === 'apply' && (
          <StepApply
            jobCount={selectedJobs.length}
            headless={headless}
            setHeadless={setHeadless}
            autoSubmit={autoSubmit}
            setAutoSubmit={setAutoSubmit}
            onLaunch={handleLaunch}
            applying={applying}
            applyError={applyError}
          />
        )}
        {STEPS[stepIdx] === 'results' && (
          <StepResults batchResult={batchResult} onRestart={handleRestart} />
        )}
      </StepFrame>
    </div>
  )
}
