import json
import asyncio
from typing import List, Optional
from datetime import datetime

from app.core.config import settings
from app.core.logger import logger
from app.integrations.aws_service import aws_service
from app.events.models import SQSMessage, EventMessage, EventType

from app.events.event_router import event_router

class SQSConsumerService:
    """Background SQS consumer service that pulls and processes messages"""
    
    def __init__(self):
        self.aws_service = aws_service
        self.is_running = False
        self.consumer_task = None
        
    async def pull_messages(
        self, 
        queue_url: str, 
        max_messages: int = 10, 
        wait_time_seconds: int = 5
    ) -> List[SQSMessage]:
        """
        Pull messages from SQS queue
        
        Args:
            queue_url: SQS queue URL
            max_messages: Maximum number of messages to retrieve
            wait_time_seconds: Long polling wait time
            
        Returns:
            List of SQS messages
        """
        try:
            logger.debug(f"Polling SQS queue: {queue_url}")
            
            # Use async AWS service method directly
            raw_messages = await self.aws_service.receive_sqs_messages(
                max_number_of_messages=max_messages,
                wait_time_seconds=wait_time_seconds
            )
            
            if not raw_messages:
                return []
            
            # Convert to SQSMessage objects
            messages = []
            for raw_msg in raw_messages:
                try:
                    sqs_msg = SQSMessage(**raw_msg)
                    messages.append(sqs_msg)
                except Exception as e:
                    logger.error(f"Failed to parse SQS message: {e}")
                    logger.error(f"Raw message: {raw_msg}")
            
            logger.info(f"Pulled {len(messages)} messages from SQS")
            return messages
            
        except Exception as e:
            logger.error(f"Error pulling messages from SQS: {e}")
            return []
    
    def parse_event_message(self, sqs_message: SQSMessage) -> Optional[EventMessage]:
        """
        Parse SQS message body to extract event information
        
        Args:
            sqs_message: SQS message object
            
        Returns:
            Parsed event message or None if parsing fails
        """
        try:
            # Parse JSON body
            body_data = json.loads(sqs_message.Body)
            
            # Handle SNS messages (they wrap the actual message)
            if 'Message' in body_data and 'TopicArn' in body_data:
                # This is an SNS message, extract the actual message
                logger.debug("Detected SNS message, extracting inner message")
                actual_message = json.loads(body_data['Message'])
            else:
                # Direct SQS message
                actual_message = body_data
            
            # Extract event type
            event_type_str = actual_message.get('event_type')
            if not event_type_str:
                logger.warning("Message missing 'event_type' field")
                return None
            
            # Validate event type
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                logger.warning(f"Unknown event type: {event_type_str}")
                return None
            
            # Create EventMessage
            event_message = EventMessage(
                event_type=event_type,
                event_id=actual_message.get('event_id', 'unknown'),
                service_name=actual_message.get('service_name', 'unknown'),
                timestamp=actual_message.get('timestamp', datetime.utcnow().isoformat()),
                data=actual_message.get('data', {}),
                metadata=actual_message.get('metadata', {})
            )
            
            logger.info(f"Parsed event: {event_type} from {event_message.service_name}")
            return event_message
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message body: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing event message: {e}")
            return None
    
    def detect_event_type(self, event_message: EventMessage) -> EventType:
        """
        Detect and return the event type
        
        Args:
            event_message: Parsed event message
            
        Returns:
            Event type enum
        """
        return event_message.event_type
    
    async def delete_message(self, queue_url: str, receipt_handle: str) -> bool:
        """
        Delete a processed message from SQS queue
        
        Args:
            queue_url: SQS queue URL
            receipt_handle: Message receipt handle
            
        Returns:
            True if deleted successfully
        """
        try:
            # Use async AWS service method directly
            result = await self.aws_service.delete_sqs_message(receipt_handle)
            
            if result:
                logger.debug("Message deleted from SQS queue")
                return True
            else:
                logger.error("Failed to delete message from SQS")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete message from SQS: {e}")
            return False
    
    async def start_background_consumer(
        self, 
        queue_url: str,
        max_messages: int = 10,
        wait_time_seconds: int = 5
    ):
        """
        Start background SQS consumer that runs continuously
        
        Args:
            queue_url: SQS queue URL
            max_messages: Maximum messages per poll
            wait_time_seconds: Long polling wait time
        """
        self.is_running = True
        logger.info(f"🔄 Starting SQS consumer for queue: {queue_url}")
        
        while self.is_running:
            try:
                # Pull messages from SQS
                sqs_messages = await self.pull_messages(
                    queue_url=queue_url,
                    max_messages=max_messages,
                    wait_time_seconds=wait_time_seconds
                )
                
                if sqs_messages:
                    logger.info(f"Processing {len(sqs_messages)} messages")
                    
                    for sqs_msg in sqs_messages:
                        try:
                            # Parse event message
                            event_msg = self.parse_event_message(sqs_msg)
                            
                            if event_msg:
                                # Detect event type
                                event_type = self.detect_event_type(event_msg)
                                logger.info(f"🎯 Detected event: {event_type}")
                                
                                # Route to appropriate service handler
                                success = await event_router.route_event(event_msg)
                                
                                if success:
                                    # Delete message after successful processing
                                    await self.delete_message(queue_url, sqs_msg.ReceiptHandle)
                                    logger.info(f"✅ Successfully processed event {event_msg.event_id}")
                                else:
                                    logger.error(f"❌ Failed to process event {event_msg.event_id}")
                            else:
                                logger.warning(f"⚠️  Failed to parse message: {sqs_msg.MessageId} - removing from queue")
                                # Delete malformed messages to prevent queue clogging
                                await self.delete_message(queue_url, sqs_msg.ReceiptHandle)
                                
                        except Exception as e:
                            logger.error(f"❌ Error processing message {sqs_msg.MessageId}: {e}")
                
                # Small delay to prevent excessive polling
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error in SQS consumer loop: {e}")
                await asyncio.sleep(5)  # Longer delay on error
    
    def stop_consumer(self):
        """Stop the background consumer"""
        self.is_running = False
        logger.info("🛑 Stopping SQS consumer")
    
    def is_consumer_running(self) -> bool:
        """Check if consumer is running"""
        return self.is_running


# Global SQS consumer instance
sqs_consumer = SQSConsumerService() 