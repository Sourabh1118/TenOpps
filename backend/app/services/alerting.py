"""
Alerting service for sending notifications to administrators.

Implements Requirements 15.5, 15.7:
- Send alerts for critical errors
- Alert on 3 consecutive scraping failures
- Alert on circuit breaker triggers
"""
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger, sanitize_log_data
from app.core.redis import redis_client

logger = get_logger(__name__)


class AlertingService:
    """
    Service for sending alerts to administrators.
    
    Supports multiple alert channels:
    - Email (SMTP)
    - Slack (webhook)
    """
    
    def __init__(self):
        """Initialize alerting service with configuration."""
        self.email_enabled = bool(
            getattr(settings, 'SMTP_HOST', None) and 
            getattr(settings, 'ADMIN_EMAIL', None)
        )
        self.slack_enabled = bool(getattr(settings, 'SLACK_WEBHOOK_URL', None))
        
        if not self.email_enabled and not self.slack_enabled:
            logger.warning(
                "No alerting channels configured. "
                "Set SMTP_HOST/ADMIN_EMAIL or SLACK_WEBHOOK_URL in environment."
            )
    
    async def send_critical_error_alert(
        self,
        error_message: str,
        error_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert for critical errors.
        
        Implements Requirement 15.5:
        - Sends alerts to administrators for critical errors
        
        Args:
            error_message: Description of the error
            error_type: Type/category of error
            context: Additional context information
            
        Returns:
            True if alert was sent successfully, False otherwise
        """
        subject = f"[CRITICAL] {error_type}: {error_message[:50]}"
        
        # Sanitize context to remove sensitive data (Requirement 15.6)
        safe_context = sanitize_log_data(context) if context else {}
        
        body = f"""
Critical Error Alert

Time: {datetime.utcnow().isoformat()}Z
Environment: {settings.APP_ENV}
Error Type: {error_type}
Message: {error_message}

Context:
{self._format_context(safe_context)}

Please investigate immediately.
"""
        
        logger.error(
            f"Critical error alert: {error_type}",
            extra={'context': safe_context}
        )
        
        return await self._send_alert(subject, body)
    
    async def send_scraping_failure_alert(
        self,
        source_platform: str,
        consecutive_failures: int,
        last_error: str
    ) -> bool:
        """
        Send alert for consecutive scraping failures.
        
        Implements Requirement 15.7:
        - Alert on 3 consecutive scraping failures
        
        Args:
            source_platform: Name of the scraping source
            consecutive_failures: Number of consecutive failures
            last_error: Last error message
            
        Returns:
            True if alert was sent successfully, False otherwise
        """
        subject = f"[ALERT] Scraping Failures: {source_platform} ({consecutive_failures} consecutive)"
        
        body = f"""
Scraping Failure Alert

Time: {datetime.utcnow().isoformat()}Z
Environment: {settings.APP_ENV}
Source Platform: {source_platform}
Consecutive Failures: {consecutive_failures}
Last Error: {last_error}

The scraping service for {source_platform} has failed {consecutive_failures} times in a row.
Please check the scraping configuration and source availability.
"""
        
        logger.error(
            f"Scraping failure alert: {source_platform}",
            extra={
                'context': {
                    'source_platform': source_platform,
                    'consecutive_failures': consecutive_failures,
                    'last_error': last_error
                }
            }
        )
        
        return await self._send_alert(subject, body)
    
    async def send_circuit_breaker_alert(
        self,
        service_name: str,
        reason: str
    ) -> bool:
        """
        Send alert when circuit breaker is triggered.
        
        Implements Requirement 15.8:
        - Alert when circuit breaker is triggered
        
        Args:
            service_name: Name of the service with circuit breaker
            reason: Reason for circuit breaker trigger
            
        Returns:
            True if alert was sent successfully, False otherwise
        """
        subject = f"[ALERT] Circuit Breaker Triggered: {service_name}"
        
        body = f"""
Circuit Breaker Alert

Time: {datetime.utcnow().isoformat()}Z
Environment: {settings.APP_ENV}
Service: {service_name}
Reason: {reason}

The circuit breaker for {service_name} has been triggered.
The service is temporarily unavailable and fallback behavior is active.
"""
        
        logger.warning(
            f"Circuit breaker triggered: {service_name}",
            extra={'context': {'service_name': service_name, 'reason': reason}}
        )
        
        return await self._send_alert(subject, body)
    
    async def _send_alert(self, subject: str, body: str) -> bool:
        """
        Send alert via all configured channels.
        
        Args:
            subject: Alert subject/title
            body: Alert body/message
            
        Returns:
            True if at least one channel succeeded, False otherwise
        """
        success = False
        
        if self.email_enabled:
            if await self._send_email_alert(subject, body):
                success = True
        
        if self.slack_enabled:
            if await self._send_slack_alert(subject, body):
                success = True
        
        return success
    
    async def _send_email_alert(self, subject: str, body: str) -> bool:
        """
        Send alert via email.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            smtp_host = getattr(settings, 'SMTP_HOST', None)
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_user = getattr(settings, 'SMTP_USER', None)
            smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)
            from_email = getattr(settings, 'FROM_EMAIL', smtp_user)
            
            if not all([smtp_host, admin_email]):
                logger.warning("Email alerting not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = admin_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {admin_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=e)
            return False
    
    async def _send_slack_alert(self, subject: str, body: str) -> bool:
        """
        Send alert via Slack webhook.
        
        Args:
            subject: Alert title
            body: Alert message
            
        Returns:
            True if Slack message was sent successfully, False otherwise
        """
        try:
            webhook_url = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            
            if not webhook_url:
                logger.warning("Slack alerting not configured")
                return False
            
            # Format message for Slack
            payload = {
                "text": f"*{subject}*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": subject
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{body}```"
                        }
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Slack alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}", exc_info=e)
            return False
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary for display in alert.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted string representation
        """
        if not context:
            return "No additional context"
        
        lines = []
        for key, value in context.items():
            lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)


# Global alerting service instance
alerting_service = AlertingService()


async def track_scraping_failures(source_platform: str, error_message: str) -> None:
    """
    Track scraping failures and send alert after 3 consecutive failures.
    
    Implements Requirement 15.7:
    - Alert on 3 consecutive scraping failures
    
    Args:
        source_platform: Name of the scraping source
        error_message: Error message from failed scraping attempt
    """
    redis = redis_client.get_cache_client()
    key = f"scraping_failures:{source_platform}"
    
    try:
        # Increment failure count
        failures = redis.incr(key)
        
        # Set expiration to 1 hour (failures reset after 1 hour of no failures)
        redis.expire(key, 3600)
        
        logger.warning(
            f"Scraping failure for {source_platform}: {failures} consecutive failures",
            extra={'context': {'source_platform': source_platform, 'failures': failures}}
        )
        
        # Send alert on 3rd consecutive failure (Requirement 15.7)
        if failures == 3:
            await alerting_service.send_scraping_failure_alert(
                source_platform=source_platform,
                consecutive_failures=failures,
                last_error=error_message
            )
        
    except Exception as e:
        logger.error(f"Failed to track scraping failures: {e}", exc_info=e)


async def reset_scraping_failures(source_platform: str) -> None:
    """
    Reset scraping failure count after successful scraping.
    
    Args:
        source_platform: Name of the scraping source
    """
    redis = redis_client.get_cache_client()
    key = f"scraping_failures:{source_platform}"
    
    try:
        redis.delete(key)
        logger.info(f"Reset scraping failure count for {source_platform}")
    except Exception as e:
        logger.error(f"Failed to reset scraping failures: {e}", exc_info=e)
