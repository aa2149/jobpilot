# ============================================================================
# Copyright (c) 2026 [YOUR NAME]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# ============================================================================
"""Email delivery — stubbed in v1.

When EMAIL_ENABLED=false (default), this module:
  - Composes a real .eml file (RFC-822 compliant, with the tracker xlsx
    as a base64 MIME attachment)
  - Writes it to logs/<batch_id>/email.eml
  - Logs a 'would_send_email' event with the recipient and subject
  - Returns the path so the API response can include it

The .eml file is a real email — you can open it in any mail client
(Apple Mail, Outlook, Thunderbird) and see exactly what would have been
sent to the user. This is honest about the limitation while making the
behavior verifiable.

To wire real email in production:
  1. pip install resend  (or sendgrid, postmark, etc.)
  2. Set EMAIL_ENABLED=true and add EMAIL_PROVIDER_API_KEY to .env
  3. Implement send_real_email() at the bottom of this file
  4. The send() function below will route to it when EMAIL_ENABLED=true

The roadmap is one block of code, not a refactor.
"""
from __future__ import annotations

import base64
import mimetypes
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

import structlog

from jobpilot.config import settings
from jobpilot.observability.logger import run_dir


def _build_email_message(
    *,
    to_addr: str,
    to_name: str,
    subject: str,
    body_text: str,
    body_html: str,
    attachment_path: Path | None,
) -> EmailMessage:
    """Compose an RFC-822 multipart message with the tracker as attachment."""
    msg = EmailMessage()
    msg["From"] = f"JobPilot <{settings.email_from}>"
    msg["To"] = f"{to_name} <{to_addr}>"
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="jobpilot.local")
    msg["X-JobPilot-Stub"] = "true"  # Marker so production code can tell stubs apart

    msg.set_content(body_text)
    msg.add_alternative(body_html, subtype="html")

    if attachment_path and attachment_path.exists():
        ctype, encoding = mimetypes.guess_type(str(attachment_path))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with attachment_path.open("rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=attachment_path.name,
        )

    return msg


def _format_results_html(applicant_name: str, batch_summary: dict, results: list) -> str:
    """Render the per-applicant email body in HTML."""
    rows_html = ""
    for r in results:
        state_color = {
            "submitted": "#1F4D3F",
            "pre_submit_ready": "#92400E",
            "blocked_by_bot_detection": "#9B2C2C",
        }.get(r.state, "#555555")
        rows_html += f"""
        <tr>
          <td style="padding: 8px 12px; border-bottom: 1px solid #E0DED4; font-family: 'Geist', sans-serif;">{r.company or '—'}</td>
          <td style="padding: 8px 12px; border-bottom: 1px solid #E0DED4; font-family: 'Geist', sans-serif;">{r.role or '—'}</td>
          <td style="padding: 8px 12px; border-bottom: 1px solid #E0DED4; font-family: 'Geist', sans-serif; color: {state_color}; font-weight: 600;">{r.state}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html>
<body style="margin: 0; padding: 0; background: #FAFAF7;">
  <div style="max-width: 600px; margin: 0 auto; padding: 40px 24px; font-family: 'Geist', system-ui, sans-serif; color: #161510;">

    <h1 style="font-family: 'Fraunces', serif; font-size: 32px; font-weight: 700; margin: 0 0 8px 0;">
      Hi {applicant_name} —
    </h1>
    <p style="font-family: 'Fraunces', serif; font-size: 18px; font-style: italic; color: #555555; margin: 0 0 32px 0;">
      JobPilot just applied to {batch_summary['total_jobs']} jobs for you.
    </p>

    <div style="display: flex; gap: 0; border: 1px solid #E0DED4; border-radius: 8px; overflow: hidden; margin-bottom: 24px;">
      <div style="padding: 16px 20px; flex: 1; border-right: 1px solid #E0DED4; background: #F2F1EB;">
        <div style="font-size: 11px; color: #777; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;">Submitted</div>
        <div style="font-size: 28px; font-weight: 700; color: #1F4D3F;">{batch_summary['successes']}</div>
      </div>
      <div style="padding: 16px 20px; flex: 1; border-right: 1px solid #E0DED4; background: #F2F1EB;">
        <div style="font-size: 11px; color: #777; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;">Blocked</div>
        <div style="font-size: 28px; font-weight: 700; color: #9B2C2C;">{batch_summary['blocked']}</div>
      </div>
      <div style="padding: 16px 20px; flex: 1; background: #F2F1EB;">
        <div style="font-size: 11px; color: #777; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;">Failed</div>
        <div style="font-size: 28px; font-weight: 700; color: #92400E;">{batch_summary['failures']}</div>
      </div>
    </div>

    <p style="font-size: 15px; line-height: 1.6; color: #4A4940;">
      Your tracker is attached as <strong>jobpilot_tracker.xlsx</strong>. Open it now —
      it has one row per company we applied to, with drop-downs for status and
      interview rounds. Update it as you hear back.
    </p>

    <h3 style="font-family: 'Fraunces', serif; font-size: 18px; font-weight: 600; margin: 32px 0 12px 0; color: #161510;">Where we applied today</h3>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid #E0DED4; border-radius: 6px; overflow: hidden;">
      <thead>
        <tr style="background: #161510; color: white;">
          <th style="padding: 10px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;">Company</th>
          <th style="padding: 10px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;">Role</th>
          <th style="padding: 10px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;">Status</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>

    <h3 style="font-family: 'Fraunces', serif; font-size: 18px; font-weight: 600; margin: 32px 0 12px 0; color: #161510;">When to follow up</h3>
    <ul style="font-size: 14px; line-height: 1.7; color: #4A4940; padding-left: 20px;">
      <li>If a company hasn't responded in <strong>21 days</strong>, mark Status as "Ghosted" — silence is data, not nothing.</li>
      <li>If you progressed to Round 1 but went silent, a polite recruiter nudge is fair after 7 days.</li>
      <li>Anything in <strong>Round 2 or further</strong>: keep notes in the tracker. Salary range, interview format, gut feel.</li>
    </ul>

    <p style="font-size: 13px; color: #777; margin: 40px 0 0 0; padding-top: 20px; border-top: 1px solid #E0DED4;">
      Sent by JobPilot · {datetime.now(timezone.utc).strftime('%Y-%m-%d')} · Batch {batch_summary.get('batch_id', '')}
    </p>
    <p style="font-size: 11px; color: #B8B5A6; margin: 4px 0 0 0; font-style: italic;">
      © 2026 [YOUR NAME]. All rights reserved.
    </p>
  </div>
</body>
</html>"""


def _format_results_text(applicant_name: str, batch_summary: dict, results: list) -> str:
    """Plain-text fallback."""
    lines = [
        f"Hi {applicant_name},",
        "",
        f"JobPilot just applied to {batch_summary['total_jobs']} jobs for you.",
        "",
        f"  Submitted:  {batch_summary['successes']}",
        f"  Blocked:    {batch_summary['blocked']}",
        f"  Failed:     {batch_summary['failures']}",
        "",
        "Your tracker is attached. Open it and update statuses as you hear back.",
        "",
        "Where we applied:",
    ]
    for r in results:
        lines.append(f"  · {r.company or '—'}: {r.state}")
    lines += [
        "",
        "When to follow up:",
        "  · 21 days of silence → mark as Ghosted. Silence is data.",
        "  · Round 1 silence after 7 days → polite recruiter nudge.",
        "",
        "Sent by JobPilot · " + datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "© 2026 [YOUR NAME]. All rights reserved.",
    ]
    return "\n".join(lines)


def send(
    *,
    batch_id: str,
    to_addr: str,
    to_name: str,
    batch_summary: dict,
    results: list,
    tracker_path: Path,
) -> Path:
    """Compose and "send" the per-batch email.

    Returns the path to the .eml file written. In stub mode (default),
    no real email is sent — but the file is a real RFC-822 email you
    can open in any mail client.
    """
    log = structlog.get_logger("jobpilot.email")

    subject = f"JobPilot — applied to {batch_summary['total_jobs']} jobs for you"
    body_text = _format_results_text(to_name, batch_summary, results)
    body_html = _format_results_html(to_name, batch_summary, results)

    msg = _build_email_message(
        to_addr=to_addr,
        to_name=to_name,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachment_path=tracker_path,
    )

    out_dir = run_dir(batch_id)
    eml_path = out_dir / "email.eml"
    with eml_path.open("wb") as f:
        f.write(bytes(msg))

    if not settings.email_enabled:
        log.info(
            "email.would_send",
            batch_id=batch_id,
            to=to_addr,
            subject=subject,
            attachment=str(tracker_path),
            eml_written=str(eml_path),
            note="EMAIL_ENABLED=false — file written but not sent. Open the .eml to preview.",
        )
        return eml_path

    # Real email path — only reached when EMAIL_ENABLED=true
    try:
        send_real_email(msg, to_addr)
        log.info("email.sent", batch_id=batch_id, to=to_addr)
    except Exception as e:
        log.warning("email.send_failed", batch_id=batch_id, error=str(e), eml_path=str(eml_path))

    return eml_path


def send_real_email(msg: EmailMessage, to_addr: str) -> None:
    """Production email send path. NOT IMPLEMENTED in v1.

    To wire this up:

    Option A — Resend (recommended, simplest):
        pip install resend
        Add RESEND_API_KEY to .env
        Then:
            import resend
            resend.api_key = settings.resend_api_key
            resend.Emails.send({
                "from": settings.email_from,
                "to": to_addr,
                "subject": msg["Subject"],
                "html": msg.get_body(preferencelist=("html",)).get_content(),
                "attachments": [{
                    "filename": "jobpilot_tracker.xlsx",
                    "content": base64.b64encode(<bytes>).decode(),
                }],
            })

    Option B — SendGrid (more configurable):
        pip install sendgrid
        Use the SendGrid SDK with attachment encoding similar to above.

    Option C — SMTP (zero-cost if you have one):
        Use python's stdlib smtplib + the EmailMessage we already built.
    """
    raise NotImplementedError(
        "Real email send is not wired in v1. "
        "Set EMAIL_ENABLED=false (default) to use the .eml stub. "
        "See send_real_email() in src/jobpilot/flow/email_stub.py for the integration roadmap."
    )
