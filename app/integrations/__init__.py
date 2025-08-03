# This package contains modules for integrating with external services.

from app.integrations.aws_service import AWSService, aws_service
from app.integrations.email_service import EmailService, email_service

__all__ = [
    'AWSService',
    'aws_service',
    'EmailService',
    'email_service',
]
