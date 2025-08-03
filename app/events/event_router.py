from typing import Dict

from app.core.logger import logger
from app.events.models import EventMessage, EventType


class EventRouter:
    """Routes events directly to appropriate service methods"""
    
    def __init__(self):
        pass
        

    async def route_event(self, event_message: EventMessage) -> bool:
        """
        Route an event directly to appropriate service methods
        
        Args:
            event_message: The event to route
            
        Returns:
            True if service method processed successfully, False otherwise
        """
        event_type = event_message.event_type
        event_data = event_message.data
        
        try:
            logger.info(f"🔄 Processing {event_type} event (ID: {event_message.event_id})")
            
            # Route directly to service methods based on event type
            if event_type == EventType.USER_CREATED:
                from app.services.user import process_external_user_created
                success = await process_external_user_created(event_data, event_message.service_name)
                if success:
                    from app.services.model import process_external_user_created as process_model_user_created
                    model_success = await process_model_user_created(event_data, event_message.service_name)
                    logger.info(f"Model auto-linking result: {model_success}")
                    
            elif event_type == EventType.USER_UPDATED:
                from app.services.user import process_external_user_updated
                success = await process_external_user_updated(event_data, event_message.service_name)
            elif event_type == EventType.USER_DELETED:
                return True
            else:
                logger.warning(f"⚠️  Unsupported event type: {event_type}")
                return False
                
            if success:
                logger.info(f"✅ Successfully processed {event_type} event")
            else:
                logger.error(f"❌ Failed to process {event_type} event")
                
            return success
            
        except ImportError as e:
            # Service method doesn't exist - that's ok, just log
            logger.info(f"⚠️  No service method for {event_type} - logged only")
            return True
        except Exception as e:
            logger.error(f"❌ Exception while routing event {event_message.event_id}: {str(e)}")
            return False


# Global event router instance
event_router = EventRouter()
