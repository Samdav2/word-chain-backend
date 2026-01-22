"""
Email service using Mailjet for transactional emails.

Handles sending verification emails, password reset emails, and welcome emails.
"""

import httpx
from typing import Optional
from app.core.config import settings


class EmailError(Exception):
    """Exception raised when email sending fails."""
    pass


async def send_email(
    to_email: str,
    to_name: Optional[str],
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email using Mailjet API.

    Args:
        to_email: Recipient email address
        to_name: Recipient name (optional)
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)

    Returns:
        True if email sent successfully

    Raises:
        EmailError: If Mailjet credentials are not configured or sending fails
    """
    if not settings.mailjet_api_key or not settings.mailjet_api_secret:
        # In development without Mailjet, just log the email
        print(f"📧 [DEV MODE] Would send email to: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Content: {text_content or html_content[:200]}...")
        return True

    payload = {
        "Messages": [
            {
                "From": {
                    "Email": settings.mailjet_sender_email,
                    "Name": settings.mailjet_sender_name
                },
                "To": [
                    {
                        "Email": to_email,
                        "Name": to_name or to_email
                    }
                ],
                "Subject": subject,
                "HTMLPart": html_content
            }
        ]
    }

    if text_content:
        payload["Messages"][0]["TextPart"] = text_content

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.mailjet.com/v3.1/send",
                json=payload,
                auth=(settings.mailjet_api_key, settings.mailjet_api_secret),
                timeout=30.0
            )

            if response.status_code == 200:
                return True
            else:
                raise EmailError(f"Mailjet API error: {response.status_code} - {response.text}")

        except httpx.RequestError as e:
            raise EmailError(f"Failed to send email: {str(e)}")


def _get_email_base_template(title: str, content: str) -> str:
    """Generate the base email template with Word Chain branding (red/orange/black/white)."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #1a1a1a;">
        <div style="max-width: 600px; margin: 0 auto;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #ff4d00 0%, #ff6b35 50%, #e63900 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: bold;">🔗 Word Chain</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">Educational Word Game</p>
            </div>

            <!-- Content -->
            <div style="background-color: #ffffff; padding: 35px; border-radius: 0 0 12px 12px;">
                {content}

                <!-- Footer -->
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        © 2026 Word Chain Game. All rights reserved.
                    </p>
                    <p style="color: #999; font-size: 11px; margin: 5px 0 0 0;">
                        This is an automated message from Word Chain.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


async def send_verification_email(email: str, token: str, name: Optional[str] = None) -> bool:
    """Send email verification link to the user."""
    verification_url = f"{settings.frontend_url}/verify-email?token={token}"

    subject = "🔐 Verify Your Word Chain Account"

    content = f"""
        <h2 style="background-color: #ff4d00; color: white; padding: 15px; border-radius: 8px; margin: 0 0 20px 0; font-size: 24px; text-align: center;">Verify Your Email</h2>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            Hi{' ' + name if name else ''},
        </p>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            Welcome to <strong>Word Chain</strong>! You're just one step away from starting your word adventure. Click the button below to verify your email address:
        </p>

        <div style="text-align: center; margin: 35px 0;">
            <a href="{verification_url}" style="background: linear-gradient(135deg, #ff4d00 0%, #ff6b35 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(255,77,0,0.3);">
                ✓ Verify Email
            </a>
        </div>

        <div style="background-color: #fff5f0; border-left: 4px solid #ff4d00; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="color: #666; font-size: 14px; margin: 0;">
                ⏰ This link will expire in <strong>24 hours</strong>.
            </p>
        </div>

        <p style="color: #999; font-size: 13px;">
            If you didn't create an account, you can safely ignore this email.
        </p>

        <p style="color: #999; font-size: 12px; margin-top: 20px; word-break: break-all;">
            Link not working? Copy this URL: <br>
            <span style="color: #ff4d00;">{verification_url}</span>
        </p>
    """

    html_content = _get_email_base_template("Verify Your Email", content)

    text_content = f"""
    Verify Your Email - Word Chain

    Hi{' ' + name if name else ''},

    Welcome to Word Chain! Please visit the following link to verify your email address:

    {verification_url}

    This link will expire in 24 hours.

    If you didn't create an account, you can safely ignore this email.
    """

    return await send_email(email, name, subject, html_content, text_content)


async def send_password_reset_email(email: str, token: str, name: Optional[str] = None) -> bool:
    """Send password reset link to the user."""
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    subject = "🔑 Reset Your Word Chain Password"

    content = f"""
        <h2 style="background-color: #ff4d00; color: white; padding: 15px; border-radius: 8px; margin: 0 0 20px 0; font-size: 24px; text-align: center;">Reset Your Password</h2>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            Hi{' ' + name if name else ''},
        </p>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            We received a request to reset your password for your <strong>Word Chain</strong> account. Click the button below to choose a new password:
        </p>

        <div style="text-align: center; margin: 35px 0;">
            <a href="{reset_url}" style="background: linear-gradient(135deg, #ff4d00 0%, #ff6b35 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(255,77,0,0.3);">
                🔑 Reset Password
            </a>
        </div>

        <div style="background-color: #fff5f0; border-left: 4px solid #ff4d00; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="color: #666; font-size: 14px; margin: 0;">
                ⏰ This link will expire in <strong>60 minutes</strong>.
            </p>
        </div>

        <div style="background-color: #1a1a1a; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="color: #ff6b35; font-size: 14px; margin: 0;">
                ⚠️ <strong>Security Notice:</strong> If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            </p>
        </div>

        <p style="color: #999; font-size: 12px; margin-top: 20px; word-break: break-all;">
            Link not working? Copy this URL: <br>
            <span style="color: #ff4d00;">{reset_url}</span>
        </p>
    """

    html_content = _get_email_base_template("Reset Your Password", content)

    text_content = f"""
    Reset Your Password - Word Chain

    Hi{' ' + name if name else ''},

    We received a request to reset your password. Please visit the following link to choose a new password:

    {reset_url}

    This link will expire in 60 minutes.

    If you didn't request a password reset, you can safely ignore this email.
    """

    return await send_email(email, name, subject, html_content, text_content)


async def send_welcome_email(email: str, name: Optional[str] = None) -> bool:
    """Send welcome email after successful email verification."""
    login_url = f"{settings.frontend_url}/login"

    subject = "🎉 Welcome to Word Chain!"

    content = f"""
        <h2 style="background-color: #ff4d00; color: white; padding: 15px; border-radius: 8px; margin: 0 0 20px 0; font-size: 24px; text-align: center;">Welcome to Word Chain! 🎉</h2>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            Hi{' ' + name if name else ''},
        </p>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            Your email has been verified and your account is now <strong style="color: #ff4d00;">fully activated!</strong> You're all set to start your learning adventure.
        </p>

        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 25px; border-radius: 10px; margin: 25px 0;">
            <h3 style="color: #ff6b35; margin: 0 0 15px 0; font-size: 18px;">What you can do now:</h3>
            <table style="width: 100%;">
                <tr>
                    <td style="padding: 8px 0; color: white; font-size: 15px;">
                        🎯 <span style="color: #fff;">Play word chain games & improve vocabulary</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: white; font-size: 15px;">
                        📊 <span style="color: #fff;">Track your learning progress with analytics</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: white; font-size: 15px;">
                        🏆 <span style="color: #fff;">Compete on the leaderboard</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: white; font-size: 15px;">
                        ⭐ <span style="color: #fff;">Earn XP and level up your skills</span>
                    </td>
                </tr>
            </table>
        </div>

        <div style="text-align: center; margin: 35px 0;">
            <a href="{login_url}" style="background: linear-gradient(135deg, #ff4d00 0%, #ff6b35 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(255,77,0,0.3);">
                🎮 Start Playing
            </a>
        </div>

        <p style="color: #666; font-size: 14px; text-align: center;">
            Happy learning! Let the word chain begin! 📚
        </p>
    """

    html_content = _get_email_base_template("Welcome to Word Chain", content)

    text_content = f"""
    Welcome to Word Chain!

    Hi{' ' + name if name else ''},

    Your email has been verified and your account is now fully activated!

    You're all set to:
    - Play word chain games and improve your vocabulary
    - Track your learning progress with analytics
    - Compete on the leaderboard
    - Earn XP and level up

    Visit {login_url} to start playing!

    Happy learning!
    """

    return await send_email(email, name, subject, html_content, text_content)


async def send_password_changed_email(email: str, name: Optional[str] = None) -> bool:
    """Send notification email when password has been changed."""
    subject = "🔒 Your Word Chain Password Was Changed"

    content = f"""
        <h2 style="background-color: #ff4d00; color: white; padding: 15px; border-radius: 8px; margin: 0 0 20px 0; font-size: 24px; text-align: center;">Password Changed</h2>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            Hi{' ' + name if name else ''},
        </p>

        <p style="color: #333; font-size: 16px; line-height: 1.6;">
            Your <strong>Word Chain</strong> password has been successfully changed.
        </p>

        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 20px; border-radius: 10px; margin: 25px 0; text-align: center;">
            <div style="font-size: 40px; margin-bottom: 10px;">✓</div>
            <p style="color: #4caf50; font-size: 16px; font-weight: bold; margin: 0;">
                Password Updated Successfully
            </p>
        </div>

        <div style="background-color: #fff5f0; border-left: 4px solid #ff4d00; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="color: #666; font-size: 14px; margin: 0;">
                ⚠️ <strong>Didn't make this change?</strong><br>
                If you did not change your password, please contact support immediately as your account may be compromised.
            </p>
        </div>

        <p style="color: #999; font-size: 13px;">
            This is an automated security notification.
        </p>
    """

    html_content = _get_email_base_template("Password Changed", content)

    text_content = f"""
    Password Changed - Word Chain

    Hi{' ' + name if name else ''},

    Your Word Chain password has been successfully changed.

    If you did not make this change, please contact support immediately as your account may be compromised.
    """

    return await send_email(email, name, subject, html_content, text_content)
