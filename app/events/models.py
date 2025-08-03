from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
import uuid


class EventType(str, Enum):
    """Supported event types that we can process and publish"""
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    MODEL_CREATED = "model_created"
    MODEL_UPDATED = "model_updated"


class ServiceTarget(str, Enum):
    """Service targeting options for event publishing"""
    ALL = "all"  # Broadcast to all services
    USER_SERVICE = "user_service"
    PROJECT_SERVICE = "project_service"
    MODEL_SERVICE = "model_service"
    SELECTION_SERVICE = "selection_service"
    NOTIFICATION_SERVICE = "notification_service"


class SQSMessage(BaseModel):
    """Raw SQS message structure"""
    MessageId: str
    ReceiptHandle: str
    Body: str
    Attributes: Optional[Dict[str, Any]] = {}
    MessageAttributes: Optional[Dict[str, Any]] = {}


class EventMessage(BaseModel):
    """Parsed event message from SQS body"""
    event_type: EventType
    event_id: str = Field(..., description="Unique event identifier")
    service_name: str = Field(..., description="Source service name")
    timestamp: datetime = Field(..., description="When the event occurred")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = True


class PublishEventRequest(BaseModel):
    """Request model for publishing events to SNS"""
    event_type: EventType
    target_services: Union[ServiceTarget, List[ServiceTarget]] = Field(
        default=ServiceTarget.ALL, 
        description="Target service(s) - 'all' or specific service names"
    )
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    source_service: str = Field(default="model_management", description="Service publishing the event")
    
    def generate_event_message(self) -> EventMessage:
        """Generate EventMessage from publish request"""
        # Convert target_services to list format for metadata
        # Note: Due to use_enum_values=True, enums are already converted to strings
        if isinstance(self.target_services, str):
            target_list = [self.target_services]
        else:
            # self.target_services is a list of strings
            target_list = list(self.target_services)
            
        return EventMessage(
            event_type=self.event_type,
            event_id=str(uuid.uuid4()),
            service_name=self.source_service,
            timestamp=datetime.utcnow(),
            data=self.data,
            metadata={
                "target_services": target_list,
                "published_at": datetime.utcnow().isoformat()
            }
        )

    class Config:
        use_enum_values = True 