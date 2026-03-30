"""
Tests for error handling and logging functionality.

Tests Requirements 15.1, 15.2, 15.3, 15.5, 15.6, 15.7, 19.1
"""
import pytest
import logging
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from app.core.logging import (
    setup_logging,
    get_logger,
    log_error_with_context,
    sanitize_log_data,
    CustomJsonFormatter
)
from app.services.alerting import (
    AlertingService,
    track_scraping_failures,
    reset_scraping_failures
)


class TestStructuredLogging:
    """Test structured logging implementation (Requirement 15.1)."""
    
    def test_json_formatter_includes_timestamp(self):
        """Test that JSON formatter includes timestamp in ISO format."""
        formatter = CustomJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = json.loads(formatter.format(record))
        
        assert 'timestamp' in formatted
        assert formatted['timestamp'].endswith('Z')
        # Verify ISO format
        datetime.fromisoformat(formatted['timestamp'].replace('Z', '+00:00'))
    
    def test_json_formatter_includes_level(self):
        """Test that JSON formatter includes log level."""
        formatter = CustomJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None
        )
        
        formatted = json.loads(formatter.format(record))
        
        assert 'level' in formatted
        assert formatted['level'] == 'ERROR'
    
    def test_json_formatter_includes_context(self):
        """Test that JSON formatter includes context fields."""
        formatter = CustomJsonFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = json.loads(formatter.format(record))
        
        assert 'app' in formatted
        assert 'env' in formatted
        assert 'logger' in formatted
        assert formatted['logger'] == 'test.module'
    
    def test_json_formatter_includes_stack_trace(self):
        """Test that JSON formatter includes stack trace for exceptions."""
        formatter = CustomJsonFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=(type(e), e, e.__traceback__)
            )
            
            formatted = json.loads(formatter.format(record))
            
            assert 'stack_trace' in formatted
            assert 'ValueError: Test error' in formatted['stack_trace']
            assert 'Traceback' in formatted['stack_trace']
    
    def test_log_error_with_context(self):
        """Test logging errors with context information."""
        logger = get_logger("test")
        
        with patch.object(logger, 'error') as mock_error:
            error = ValueError("Test error")
            context = {'user_id': '123', 'action': 'test_action'}
            
            log_error_with_context(
                logger,
                "An error occurred",
                error=error,
                context=context
            )
            
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert call_args[0][0] == "An error occurred"
            assert call_args[1]['exc_info'] == error
            assert call_args[1]['extra']['context'] == context


class TestSensitiveDataSanitization:
    """Test sensitive data sanitization (Requirement 15.6)."""
    
    def test_sanitize_password_field(self):
        """Test that password fields are sanitized."""
        data = {
            'username': 'testuser',
            'password': 'secret123',
            'email': 'test@example.com'
        }
        
        sanitized = sanitize_log_data(data)
        
        assert sanitized['username'] == 'testuser'
        assert sanitized['password'] == '***REDACTED***'
        assert sanitized['email'] == 'test@example.com'
    
    def test_sanitize_token_fields(self):
        """Test that token fields are sanitized."""
        data = {
            'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
            'refresh_token': 'refresh_token_value',
            'api_key': 'sk_test_123456',
            'user_id': '123'
        }
        
        sanitized = sanitize_log_data(data)
        
        assert sanitized['access_token'] == '***REDACTED***'
        assert sanitized['refresh_token'] == '***REDACTED***'
        assert sanitized['api_key'] == '***REDACTED***'
        assert sanitized['user_id'] == '123'
    
    def test_sanitize_nested_data(self):
        """Test that nested sensitive data is sanitized."""
        data = {
            'user': {
                'id': '123',
                'email': 'test@example.com',
                'password_hash': 'hashed_password'
            },
            'request': {
                'headers': {
                    'authorization': 'Bearer token123'
                }
            }
        }
        
        sanitized = sanitize_log_data(data)
        
        assert sanitized['user']['id'] == '123'
        assert sanitized['user']['password_hash'] == '***REDACTED***'
        assert sanitized['request']['headers']['authorization'] == '***REDACTED***'
    
    def test_sanitize_case_insensitive(self):
        """Test that sanitization is case-insensitive."""
        data = {
            'Password': 'secret',
            'ACCESS_TOKEN': 'token',
            'Api_Key': 'key'
        }
        
        sanitized = sanitize_log_data(data)
        
        assert sanitized['Password'] == '***REDACTED***'
        assert sanitized['ACCESS_TOKEN'] == '***REDACTED***'
        assert sanitized['Api_Key'] == '***REDACTED***'


class TestAlertingService:
    """Test alerting service (Requirements 15.5, 15.7)."""
    
    @pytest.mark.asyncio
    async def test_send_critical_error_alert_email(self):
        """Test sending critical error alert via email."""
        with patch('app.services.alerting.smtplib.SMTP') as mock_smtp:
            with patch('app.services.alerting.settings') as mock_settings:
                mock_settings.SMTP_HOST = 'smtp.example.com'
                mock_settings.SMTP_PORT = 587
                mock_settings.SMTP_USER = 'user@example.com'
                mock_settings.SMTP_PASSWORD = 'password'
                mock_settings.ADMIN_EMAIL = 'admin@example.com'
                mock_settings.FROM_EMAIL = 'noreply@example.com'
                mock_settings.APP_ENV = 'production'
                mock_settings.SLACK_WEBHOOK_URL = None
                
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__.return_value = mock_server
                
                service = AlertingService()
                result = await service.send_critical_error_alert(
                    error_message="Database connection failed",
                    error_type="DatabaseError",
                    context={'database': 'postgresql'}
                )
                
                assert result is True
                mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_critical_error_alert_slack(self):
        """Test sending critical error alert via Slack."""
        with patch('app.services.alerting.requests.post') as mock_post:
            with patch('app.services.alerting.settings') as mock_settings:
                mock_settings.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/test'
                mock_settings.SMTP_HOST = None
                mock_settings.ADMIN_EMAIL = None
                mock_settings.APP_ENV = 'production'
                
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response
                
                service = AlertingService()
                result = await service.send_critical_error_alert(
                    error_message="API rate limit exceeded",
                    error_type="RateLimitError",
                    context={'endpoint': '/api/jobs'}
                )
                
                assert result is True
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert 'CRITICAL' in call_args[1]['json']['text']
    
    @pytest.mark.asyncio
    async def test_send_scraping_failure_alert(self):
        """Test sending scraping failure alert (Requirement 15.7)."""
        with patch('app.services.alerting.requests.post') as mock_post:
            with patch('app.services.alerting.settings') as mock_settings:
                mock_settings.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/test'
                mock_settings.SMTP_HOST = None
                mock_settings.ADMIN_EMAIL = None
                mock_settings.APP_ENV = 'production'
                
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response
                
                service = AlertingService()
                result = await service.send_scraping_failure_alert(
                    source_platform="linkedin",
                    consecutive_failures=3,
                    last_error="Connection timeout"
                )
                
                assert result is True
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                payload = call_args[1]['json']
                assert 'linkedin' in payload['text']
                assert '3' in str(payload)
    
    @pytest.mark.asyncio
    async def test_send_circuit_breaker_alert(self):
        """Test sending circuit breaker alert (Requirement 15.8)."""
        with patch('app.services.alerting.requests.post') as mock_post:
            with patch('app.services.alerting.settings') as mock_settings:
                mock_settings.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/test'
                mock_settings.SMTP_HOST = None
                mock_settings.ADMIN_EMAIL = None
                mock_settings.APP_ENV = 'production'
                
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response
                
                service = AlertingService()
                result = await service.send_circuit_breaker_alert(
                    service_name="payment_service",
                    reason="Too many failures"
                )
                
                assert result is True
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                payload = call_args[1]['json']
                assert 'Circuit Breaker' in payload['text']
                assert 'payment_service' in str(payload)


class TestScrapingFailureTracking:
    """Test scraping failure tracking (Requirement 15.7)."""
    
    @pytest.mark.asyncio
    async def test_track_scraping_failures_increments_count(self):
        """Test that scraping failures are tracked and incremented."""
        with patch('app.services.alerting.redis_client') as mock_redis_client:
            mock_redis = MagicMock()
            mock_redis.incr.return_value = 1
            mock_redis_client.get_cache_client.return_value = mock_redis
            
            await track_scraping_failures("linkedin", "Connection timeout")
            
            mock_redis.incr.assert_called_once_with("scraping_failures:linkedin")
            mock_redis.expire.assert_called_once_with("scraping_failures:linkedin", 3600)
    
    @pytest.mark.asyncio
    async def test_track_scraping_failures_sends_alert_on_third_failure(self):
        """Test that alert is sent on 3rd consecutive failure (Requirement 15.7)."""
        with patch('app.services.alerting.redis_client') as mock_redis_client:
            with patch('app.services.alerting.alerting_service') as mock_alerting:
                mock_redis = MagicMock()
                mock_redis.incr.return_value = 3  # Third failure
                mock_redis_client.get_cache_client.return_value = mock_redis
                
                mock_alerting.send_scraping_failure_alert = AsyncMock()
                
                await track_scraping_failures("indeed", "API error")
                
                mock_alerting.send_scraping_failure_alert.assert_called_once_with(
                    source_platform="indeed",
                    consecutive_failures=3,
                    last_error="API error"
                )
    
    @pytest.mark.asyncio
    async def test_track_scraping_failures_no_alert_before_third(self):
        """Test that no alert is sent before 3rd failure."""
        with patch('app.services.alerting.redis_client') as mock_redis_client:
            with patch('app.services.alerting.alerting_service') as mock_alerting:
                mock_redis = MagicMock()
                mock_redis.incr.return_value = 2  # Second failure
                mock_redis_client.get_cache_client.return_value = mock_redis
                
                mock_alerting.send_scraping_failure_alert = AsyncMock()
                
                await track_scraping_failures("naukri", "Timeout")
                
                mock_alerting.send_scraping_failure_alert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reset_scraping_failures(self):
        """Test resetting scraping failure count after success."""
        with patch('app.services.alerting.redis_client') as mock_redis_client:
            mock_redis = MagicMock()
            mock_redis_client.get_cache_client.return_value = mock_redis
            
            await reset_scraping_failures("monster")
            
            mock_redis.delete.assert_called_once_with("scraping_failures:monster")


class TestDatabaseErrorLogging:
    """Test database error logging (Requirement 15.3)."""
    
    def test_database_error_handler_logs_with_context(self):
        """Test that database errors are logged with query context."""
        from sqlalchemy.exc import OperationalError
        from unittest.mock import MagicMock
        
        # Create mock exception context
        mock_context = MagicMock()
        mock_context.original_exception = OperationalError("Connection failed", None, None)
        mock_context.is_disconnect = True
        mock_context.statement = "SELECT * FROM jobs WHERE id = :id"
        mock_context.parameters = {'id': '123'}
        
        with patch('app.db.session.log_error_with_context') as mock_log:
            from app.db.session import handle_db_error
            
            handle_db_error(mock_context)
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            # call_args[0] is a tuple of positional args, first is the logger
            assert 'Database error occurred' in call_args[0][1]  # Second arg is the message
            assert call_args[1]['context']['error_type'] == 'OperationalError'
            assert call_args[1]['context']['is_disconnect'] is True
            assert 'statement' in call_args[1]['context']
    
    def test_database_error_handler_sanitizes_passwords(self):
        """Test that database errors sanitize password data (Requirement 15.6)."""
        from sqlalchemy.exc import IntegrityError
        from unittest.mock import MagicMock
        
        # Create mock exception context with password in statement
        mock_context = MagicMock()
        mock_context.original_exception = IntegrityError("Duplicate key", None, None)
        mock_context.is_disconnect = False
        mock_context.statement = "INSERT INTO users (email, password) VALUES (:email, :password)"
        mock_context.parameters = {'email': 'test@example.com', 'password': 'secret123'}
        
        with patch('app.db.session.log_error_with_context') as mock_log:
            from app.db.session import handle_db_error
            
            handle_db_error(mock_context)
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            context = call_args[1]['context']
            
            # Statement should be sanitized
            assert '[SANITIZED]' in context['statement']
            
            # Parameters should be sanitized
            assert context['parameters']['password'] == '***REDACTED***'
            assert context['parameters']['email'] == 'test@example.com'



