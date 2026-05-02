#!/usr/bin/env python3
"""
Run this from /Users/ahmednawaz/Downloads/final/jobpilot:
  python3 patch_fix.py
"""
import re, shutil, sys
from pathlib import Path

BASE = Path("/Users/ahmednawaz/Downloads/final/jobpilot")

def patch(rel, old, new, label):
    f = BASE / rel
    if not f.exists():
        print(f"  ✗  Not found: {f}")
        return False
    src = f.read_text()
    if old not in src:
        print(f"  ~  Already patched or not found: {label}")
        return True
    shutil.copy(f, str(f) + ".bak")
    f.write_text(src.replace(old, new))
    print(f"  ✓  {label}")
    return True

print("\nPatching JobPilot...\n")

# ── Fix 1: schemas.py ────────────────────────────────────────────
# Make linkedin/github/portfolio accept plain strings (not strict HttpUrl)
# Make resume_path optional with empty-string default
# Add resume_saved_path field for uploaded files

patch(
    "src/jobpilot/api/schemas.py",
    """class Applicant(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: HttpUrl | None = None
    github: HttpUrl | None = None
    portfolio: HttpUrl | None = None
    resume_path: str = Field(..., description=\"Absolute path to a local PDF resume.\")
    resume_text: str = Field(..., description=\"Full text/markdown of the resume, used by the LLM.\")
    work_auth: str | None = None
    preferred_pronouns: str | None = None""",
    """class Applicant(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    resume_path: str = Field(default=\"\", description=\"Absolute path to a local PDF resume. Leave blank if uploading via /upload-resume.\")
    resume_text: str = Field(default=\"\", description=\"Full text/markdown of the resume, used by the LLM.\")
    work_auth: str | None = None
    preferred_pronouns: str | None = None""",
    "schemas.py — relax HttpUrl fields, make resume_path optional"
)

# ── Fix 2: server.py — add /upload-resume endpoint ───────────────
patch(
    "src/jobpilot/api/server.py",
    "from fastapi import FastAPI, HTTPException",
    """from fastapi import FastAPI, HTTPException, UploadFile, File
import shutil, tempfile, os""",
    "server.py — import UploadFile"
)

patch(
    "src/jobpilot/api/server.py",
    "@app.get(\"/health\")",
    """@app.post(\"/upload-resume\")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    \"\"\"
    Upload a resume PDF. Returns the saved path to pass as resume_path in /apply or /batch.
    The file is saved to a temp directory that persists for the server session.
    \"\"\"
    if not file.filename.lower().endswith((\".pdf\", \".doc\", \".docx\", \".txt\")):
        raise HTTPException(status_code=400, detail=\"Unsupported file type. Use PDF, DOC, DOCX, or TXT.\")
    upload_dir = Path(tempfile.gettempdir()) / \"jobpilot_uploads\"
    upload_dir.mkdir(exist_ok=True)
    dest = upload_dir / file.filename
    with dest.open(\"wb\") as out:
        shutil.copyfileobj(file.file, out)
    return {\"resume_path\": str(dest), \"filename\": file.filename, \"size_bytes\": dest.stat().st_size}


@app.get(\"/health\")""",
    "server.py — add /upload-resume endpoint"
)

# Need Path import in server
patch(
    "src/jobpilot/api/server.py",
    "import shutil, tempfile, os",
    "import shutil, tempfile, os\nfrom pathlib import Path",
    "server.py — add Path import"
)

# ── Fix 3: App.jsx — replace resume_path text input with file upload ──
# Find the resume_path input and replace with upload widget
OLD_RESUME_INPUT = """          <input type=\"text\" value={applicant.resume_path} onChange={(e) => setApplicant({ ...applicant, resume_path: e.target.value })} placeholder=\"/Users/you/resume.pdf\" className=\"form-input font-mono text-xs\" />"""

NEW_RESUME_INPUT = """          <ResumeUpload applicant={applicant} setApplicant={setApplicant} />"""

patch("frontend/src/App.jsx", OLD_RESUME_INPUT, NEW_RESUME_INPUT,
      "App.jsx — replace path input with upload widget")

# ── Fix 4: App.jsx — add the ResumeUpload component ──────────────
OLD_STEP_REVIEW = "// Step 4: Review — collect resume + applicant details"
NEW_STEP_REVIEW = """// Resume upload sub-component
function ResumeUpload({ applicant, setApplicant }) {
  const [uploading, setUploading] = React.useState(false)
  const [uploaded, setUploaded] = React.useState(applicant.resume_path ? applicant.resume_path.split('/').pop() : null)
  const [err, setErr] = React.useState(null)

  async function handleFile(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true); setErr(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/upload-resume', { method: 'POST', body: form })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Upload failed') }
      const data = await res.json()
      setApplicant({ ...applicant, resume_path: data.resume_path })
      setUploaded(data.filename)
    } catch (e) {
      setErr(e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <label
        htmlFor="resume-upload"
        style={{
          display: 'flex', alignItems: 'center', gap: '10px',
          border: '1.5px dashed', borderColor: uploaded ? '#c8a882' : '#ccc',
          borderRadius: '8px', padding: '14px 16px', cursor: 'pointer',
          background: uploaded ? '#fdf8f3' : '#fafafa', transition: 'all 0.2s'
        }}
      >
        <span style={{ fontSize: '20px' }}>{uploading ? '⏳' : uploaded ? '✅' : '📄'}</span>
        <span style={{ fontSize: '13px', color: '#555' }}>
          {uploading ? 'Uploading…' : uploaded ? uploaded : 'Click to upload your resume (PDF, DOC, DOCX)'}
        </span>
        <input id="resume-upload" type="file" accept=".pdf,.doc,.docx,.txt" onChange={handleFile} style={{ display: 'none' }} />
      </label>
      {err && <p style={{ color: '#c0392b', fontSize: '12px', marginTop: '6px' }}>{err}</p>}
    </div>
  )
}

// Step 4: Review — collect resume + applicant details"""

patch("frontend/src/App.jsx", OLD_STEP_REVIEW, NEW_STEP_REVIEW,
      "App.jsx — add ResumeUpload component")

# ── Fix 5: App.jsx — fix canAdvance to not require resume_path text ──
patch(
    "frontend/src/App.jsx",
    "const canAdvance = applicant.first_name && applicant.last_name && applicant.email && applicant.resume_path && applicant.resume_text",
    "const canAdvance = applicant.first_name && applicant.last_name && applicant.email && applicant.resume_path",
    "App.jsx — fix canAdvance (only require uploaded resume_path)"
)

# ── Fix 6: api.js — fix error message to show actual Pydantic detail ──
patch(
    "frontend/src/lib/api.js",
    "    const detail = data?.detail || res.statusText",
    "    const detail = Array.isArray(data?.detail) ? data.detail.map(e => e.msg + ' (' + (e.loc||[]).join('.') + ')').join('; ') : (data?.detail || res.statusText)",
    "api.js — show real Pydantic validation errors"
)

print("\nDone! Now restart the API server:\n")
print("  lsof -ti:8000 | xargs kill -9")
print("  poetry run uvicorn jobpilot.api.server:app --reload --port 8000\n")
