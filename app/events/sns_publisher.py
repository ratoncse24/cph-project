import json
from typing import Optional, List, Union
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.integrations.aws_service import aws_service
from app.events.models import EventMessage, PublishEventRequest, EventType, ServiceTarget


class SNSPublisherService:
    """Service for publishing events to SNS topics with service targeting"""
    
    def __init__(self):
        self.aws_service = aws_service
        self.topic_arn = settings.AWS_SNS_EVENTS_TOPIC_ARN
    
    async def publish_event(self, publish_request: PublishEventRequest) -> Optional[str]:
        """
        Publish an event to SNS topic
        
        Args:
            publish_request: Event publish request with targeting
            
        Returns:
            Message ID if successful, None otherwise
        """
        try:
            if not self.topic_arn:
                logger.error("SNS topic ARN not configured. Cannot publish event.")
                return None
            
            # Generate event message
            event_message = publish_request.generate_event_message()
            
            # Prepare SNS message
            message_body = event_message.model_dump_json()
            
            # Add service targeting as message attributes
            target_services = self._get_target_services(publish_request.target_services)
            message_attributes = {
                "event_type": {
                    "DataType": "String",
                    "StringValue": event_message.event_type
                },
                "target_services": {
                    "DataType": "String.Array",
                    "StringValue": json.dumps(target_services)
                },
                "source_service": {
                    "DataType": "String",
                    "StringValue": event_message.service_name
                }
            }
            
            # Publish to SNS (Standard queue - no FIFO parameters needed)
            message_id = await self.aws_service.publish_sns_message(
                topic_arn=self.topic_arn,
                message=message_body,
                subject=f"Event: {event_message.event_type}",
                message_attributes=message_attributes
            )
            
            if message_id:
                logger.info(f"✅ Published event {event_message.event_id} ({event_message.event_type}) to SNS")
                logger.info(f"   Target services: {target_services}")
                logger.info(f"   Message ID: {message_id}")
            else:
                logger.error(f"❌ Failed to publish event {event_message.event_id}")
                
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Error publishing event: {e}")
            return None
    
    def _get_target_services(self, target_services: Union[ServiceTarget, List[ServiceTarget]]) -> List[str]:
        """Convert target services to list of service names"""
        # Note: Due to use_enum_values=True, enums are already converted to strings
        if isinstance(target_services, str):
            return [target_services]
        else:
            # target_services is a list of strings
            return list(target_services)
    
    def is_configured(self) -> bool:
        """Check if SNS publisher is properly configured"""
        return bool(self.topic_arn and self.aws_service.session_params.get('region_name'))
    
    def get_topic_info(self) -> dict:
        """Get SNS topic information"""
        return {
            "topic_arn": self.topic_arn,
            "configured": self.is_configured(),
            "aws_region": settings.AWS_REGION
        }


# Global SNS publisher instance
sns_publisher = SNSPublisherService() 