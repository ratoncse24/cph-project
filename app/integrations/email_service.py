import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Union
from pathlib import Path
import os

from app.core.config import settings
from app.core.logger import logger


class EmailService:
    """
    Email service for sending emails via SMTP
    Supports text, HTML emails, and file attachments
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = settings.SMTP_HOST,
        smtp_port: int = settings.SMTP_PORT,
        smtp_username: Optional[str] = settings.SMTP_USERNAME,
        smtp_password: Optional[str] = settings.SMTP_PASSWORD,
        use_tls: bool = settings.SMTP_USE_TLS,
        email_from: Optional[str] = settings.EMAIL_FROM
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.email_from = email_from or smtp_username
        
        # Validate configuration
        if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
            logger.warning("Email service not fully configured. Some functionality may be unavailable.")
    
    def _create_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """Create and return an authenticated SMTP connection"""
        try:
            # Create SMTP connection
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls(context=ssl.create_default_context())
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=ssl.create_default_context())
            
            # Authenticate
            server.login(self.smtp_username, self.smtp_password)
            logger.debug(f"SMTP connection established with {self.smtp_host}")
            return server
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return None
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating SMTP connection: {e}")
            return None
    
    def send_email(
        self,
        to_emails: Union[str, List[str]],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc_emails: Optional[Union[str, List[str]]] = None,
        bcc_emails: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[str]] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an email with optional HTML content and attachments
        
        Args:
            to_emails: Email address(es) to send to
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            cc_emails: Optional CC email addresses
            bcc_emails: Optional BCC email addresses
            attachments: Optional list of file paths to attach
            from_email: Optional custom from email (defaults to configured from_email)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_host or not self.smtp_username or not self.smtp_password:
            logger.error("Email service not configured. Cannot send email.")
            return False
        
        try:
            # Normalize email lists
            to_list = [to_emails] if isinstance(to_emails, str) else to_emails
            cc_list = [cc_emails] if isinstance(cc_emails, str) else (cc_emails or [])
            bcc_list = [bcc_emails] if isinstance(bcc_emails, str) else (bcc_emails or [])
            sender_email = from_email or self.email_from
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender_email
            message["To"] = ", ".join(to_list)
            
            if cc_list:
                message["Cc"] = ", ".join(cc_list)
            
            # Add text content
            text_part = MIMEText(body, "plain")
            message.attach(text_part)
            
            # Add HTML content if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        filename = Path(file_path).name
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        message.attach(part)
                    else:
                        logger.warning(f"Attachment file not found: {file_path}")
            
            # Create SMTP connection and send
            server = self._create_smtp_connection()
            if not server:
                return False
            
            # Combine all recipients
            all_recipients = to_list + cc_list + bcc_list
            
            # Send email
            server.sendmail(sender_email, all_recipients, message.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {len(all_recipients)} recipients")
            logger.debug(f"Email sent - Subject: {subject}, To: {to_list}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    

    def test_email_configuration(self) -> bool:
        """Test email configuration by sending a test email to the configured sender"""
        if not self.smtp_username:
            logger.error("Cannot test email configuration: no username configured")
            return False
        
        return self.send_email(
            to_emails=self.smtp_username,
            subject="Email Configuration Test",
            body="This is a test email to verify your email configuration is working correctly.",
            html_body="<p>This is a test email to verify your email configuration is working correctly.</p>"
        )


# Create a global instance
email_service = EmailService() 