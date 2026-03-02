"""
SendGrid email service for Human-in-the-Loop escalation.
Sends escalation emails with a reply link back to the supervisor panel.
"""
import os
import logging
import urllib.parse
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, ReplyTo

logger = logging.getLogger(__name__)


def _get_app_base_url() -> str:
    """Get the frontend app base URL for supervisor reply links (used in escalation email)."""
    # Explicit public URL so the "Reply to Customer" link works when opened from email (e.g. in production)
    public = os.environ.get("APP_PUBLIC_URL", "").strip()
    if public:
        return public.rstrip("/")
    cors = os.environ.get("CORS_ORIGINS", "")
    if cors and cors != "*":
        return cors.split(",")[0].strip().rstrip("/")
    return "http://localhost:5173"


def send_escalation_email(user_query: str, session_id: str, context: str) -> bool:
    """Send an escalation email to the supervisor when activity/variation is unavailable."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    sender = os.environ.get("SENDER_EMAIL")
    supervisor = os.environ.get("SUPERVISOR_EMAIL")

    if not all([api_key, sender, supervisor]):
        logger.warning("SendGrid not configured — email escalation skipped")
        return False

    base_url = _get_app_base_url()
    encoded_query = urllib.parse.quote(user_query, safe="")
    reply_link = f"{base_url}/supervisor/{session_id}?query={encoded_query}"

    subject = f"[Dubai Travel Assistant] Customer Escalation — Session {session_id[:8]}"

    html_content = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f0f2f5;">
        <div style="background: #075E54; color: white; padding: 24px; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0; font-size: 20px;">Dubai Travel Assistant</h2>
            <p style="margin: 4px 0 0; opacity: 0.8; font-size: 14px;">Customer Escalation Request</p>
        </div>
        <div style="background: white; padding: 24px; border: 1px solid #e0e0e0; border-top: none;">
            <p style="margin: 0 0 4px; font-size: 12px; color: #8696a0; text-transform: uppercase; letter-spacing: 0.5px;">Session ID</p>
            <p style="margin: 0 0 16px; font-size: 14px; color: #111b21; font-weight: 600;">{session_id}</p>
            
            <p style="margin: 0 0 4px; font-size: 12px; color: #8696a0; text-transform: uppercase; letter-spacing: 0.5px;">Customer's Request</p>
            <div style="background: #d9fdd3; padding: 12px 16px; border-radius: 0 8px 8px 8px; margin: 0 0 16px; font-size: 14px; color: #111b21;">
                {user_query}
            </div>
            
            <p style="margin: 0 0 4px; font-size: 12px; color: #8696a0; text-transform: uppercase; letter-spacing: 0.5px;">Escalation Reason</p>
            <p style="margin: 0 0 20px; font-size: 14px; color: #667781;">{context}</p>
            
            <div style="border-top: 1px solid #e8e8e8; padding-top: 20px; text-align: center;">
                <a href="{reply_link}" style="display: inline-block; background: #075E54; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;">
                    Reply to Customer
                </a>
                <p style="margin: 12px 0 0; font-size: 12px; color: #8696a0;">
                    Click the button above to open the supervisor panel and send your reply directly to the customer's chat.
                </p>
                <p style="margin: 8px 0 0; font-size: 12px; color: #8696a0;">
                    You can also reply to this email — your reply will be relayed to the customer's chat.
                </p>
            </div>
        </div>
        <div style="background: #f9f9f9; padding: 16px; border-radius: 0 0 12px 12px; border: 1px solid #e0e0e0; border-top: none;">
            <p style="margin: 0; font-size: 11px; color: #8696a0; text-align: center;">
                This is an automated message from the Dubai Travel Assistant system.
            </p>
        </div>
    </body>
    </html>
    """

    message = Mail(
        from_email=sender,
        to_emails=supervisor,
        subject=subject,
        html_content=html_content,
    )
    # Optional: Reply-To for reply-by-email (e.g. reply-sess-xxx@inbound.yourdomain.com)
    inbound_domain = os.environ.get("INBOUND_REPLY_DOMAIN", "").strip()
    if inbound_domain:
        safe_sid = session_id.replace("@", "-").strip()
        message.reply_to = ReplyTo(f"reply-{safe_sid}@{inbound_domain}")

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logger.info(f"Escalation email sent to {supervisor}: status={response.status_code}")
        return response.status_code in (200, 201, 202)
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg:
            logger.error(
                f"SendGrid 403 Forbidden — Sender email '{sender}' likely needs verification. "
                f"Go to SendGrid Dashboard → Settings → Sender Authentication to verify."
            )
        else:
            logger.error(f"Failed to send escalation email: {e}")
        return False
