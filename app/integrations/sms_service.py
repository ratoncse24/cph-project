# from typing import Optional, List, Dict, Any
# import re
# from datetime import datetime

# from app.core.config import settings
# from app.core.logger import logger

# # Twilio will be imported conditionally
# try:
#     from twilio.rest import Client
#     from twilio.base.exceptions import TwilioException
#     TWILIO_AVAILABLE = True
# except ImportError:
#     TWILIO_AVAILABLE = False
#     logger.warning("Twilio SDK not installed. SMS functionality will be disabled.")


# class SMSService:
#     """
#     SMS service for sending text messages via Twilio
#     Supports single messages, bulk messaging, and various message types
#     """
    
#     def __init__(
#         self,
#         account_sid: Optional[str] = settings.SMS_ACCOUNT_SID,
#         auth_token: Optional[str] = settings.SMS_AUTH_TOKEN,
#         from_number: Optional[str] = settings.SMS_FROM_NUMBER,
#         enabled: bool = settings.SMS_ENABLED
#     ):
#         self.account_sid = account_sid
#         self.auth_token = auth_token
#         self.from_number = from_number
#         self.enabled = enabled
#         self.client = None
        
#         # Initialize Twilio client if configured and enabled
#         if self.enabled and TWILIO_AVAILABLE and self.account_sid and self.auth_token:
#             try:
#                 self.client = Client(self.account_sid, self.auth_token)
#                 logger.info("SMS service initialized successfully with Twilio")
#             except Exception as e:
#                 logger.error(f"Failed to initialize Twilio client: {e}")
#                 self.client = None
#         elif not TWILIO_AVAILABLE:
#             logger.warning("Twilio SDK not available. Install with: pip install twilio")
#         elif not self.enabled:
#             logger.info("SMS service disabled in configuration")
#         else:
#             logger.warning("SMS service not fully configured. Missing account_sid or auth_token.")
    
#     def _validate_phone_number(self, phone_number: str) -> str:
#         """
#         Validate and format phone number
        
#         Args:
#             phone_number: Phone number to validate
            
#         Returns:
#             str: Formatted phone number
            
#         Raises:
#             ValueError: If phone number is invalid
#         """
#         # Remove all non-digit characters except + at the beginning
#         cleaned = re.sub(r'[^\d+]', '', phone_number)
        
#         # Ensure number starts with +
#         if not cleaned.startswith('+'):
#             # Assume US number if no country code
#             if len(cleaned) == 10:
#                 cleaned = '+1' + cleaned
#             elif len(cleaned) == 11 and cleaned.startswith('1'):
#                 cleaned = '+' + cleaned
#             else:
#                 raise ValueError(f"Invalid phone number format: {phone_number}")
        
#         # Basic validation
#         if len(cleaned) < 10 or len(cleaned) > 16:
#             raise ValueError(f"Invalid phone number length: {phone_number}")
        
#         return cleaned
    
#     def send_sms(
#         self,
#         to_number: str,
#         message: str,
#         from_number: Optional[str] = None
#     ) -> Optional[str]:
#         """
#         Send a single SMS message
        
#         Args:
#             to_number: Recipient phone number
#             message: Message content (max 1600 characters)
#             from_number: Optional custom sender number
            
#         Returns:
#             str: Message SID if successful, None if failed
#         """
#         if not self.enabled:
#             logger.warning("SMS service is disabled")
#             return None
        
#         if not self.client:
#             logger.error("SMS client not initialized. Cannot send SMS.")
#             return None
        
#         try:
#             # Validate and format phone number
#             formatted_to = self._validate_phone_number(to_number)
#             sender_number = from_number or self.from_number
            
#             if not sender_number:
#                 logger.error("No sender phone number configured")
#                 return None
            
#             # Validate message length
#             if len(message) > 1600:
#                 logger.warning(f"Message too long ({len(message)} chars). Truncating to 1600 characters.")
#                 message = message[:1597] + "..."
            
#             # Send SMS
#             message_obj = self.client.messages.create(
#                 body=message,
#                 from_=sender_number,
#                 to=formatted_to
#             )
            
#             logger.info(f"SMS sent successfully to {formatted_to}. SID: {message_obj.sid}")
#             return message_obj.sid
            
#         except ValueError as e:
#             logger.error(f"Invalid phone number: {e}")
#             return None
#         except TwilioException as e:
#             logger.error(f"Twilio error sending SMS to {to_number}: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"Unexpected error sending SMS to {to_number}: {e}")
#             return None
    
#     def send_verification_code(self, to_number: str, code: str) -> Optional[str]:
#         """Send a verification code via SMS"""
#         message = f"Your verification code for {settings.PROJECT_NAME} is: {code}. This code will expire in 10 minutes."
#         return self.send_sms(to_number, message)
    
#     def send_welcome_sms(self, to_number: str, user_name: str) -> Optional[str]:
#         """Send a welcome SMS to new users"""
#         message = f"Hi {user_name}! Welcome to {settings.PROJECT_NAME}. Your account has been created successfully."
#         return self.send_sms(to_number, message)
    
#     def send_password_reset_sms(self, to_number: str, reset_code: str) -> Optional[str]:
#         """Send password reset code via SMS"""
#         message = f"Your password reset code for {settings.PROJECT_NAME} is: {reset_code}. This code expires in 15 minutes."
#         return self.send_sms(to_number, message)
    
#     def send_notification_sms(self, to_number: str, title: str, message: str) -> Optional[str]:
#         """Send a notification SMS"""
#         full_message = f"{title}: {message}"
#         return self.send_sms(to_number, full_message)
    
#     def send_bulk_sms(
#         self,
#         recipients: List[Dict[str, str]],
#         message_template: str
#     ) -> Dict[str, Optional[str]]:
#         """
#         Send personalized SMS messages to multiple recipients
        
#         Args:
#             recipients: List of dicts with 'phone' and other personalization fields
#             message_template: Message template (can contain {field} placeholders)
            
#         Returns:
#             Dict mapping phone numbers to message SIDs (or None if failed)
#         """
#         results = {}
        
#         for recipient in recipients:
#             try:
#                 phone = recipient.get('phone')
#                 if not phone:
#                     logger.error(f"No phone number provided for recipient: {recipient}")
#                     results[str(recipient)] = None
#                     continue
                
#                 # Personalize message
#                 personalized_message = message_template.format(**recipient)
                
#                 # Send SMS
#                 message_sid = self.send_sms(phone, personalized_message)
#                 results[phone] = message_sid
                
#             except KeyError as e:
#                 logger.error(f"Missing field {e} for recipient {recipient.get('phone', 'unknown')}")
#                 results[recipient.get('phone', 'unknown')] = None
#             except Exception as e:
#                 logger.error(f"Failed to send SMS to {recipient.get('phone', 'unknown')}: {e}")
#                 results[recipient.get('phone', 'unknown')] = None
        
#         successful = sum(1 for sid in results.values() if sid is not None)
#         logger.info(f"Bulk SMS completed. Success rate: {successful}/{len(results)}")
#         return results
    
#     def get_message_status(self, message_sid: str) -> Optional[Dict[str, Any]]:
#         """
#         Get the status of a sent message
        
#         Args:
#             message_sid: Twilio message SID
            
#         Returns:
#             Dict with message status information
#         """
#         if not self.client:
#             logger.error("SMS client not initialized")
#             return None
        
#         try:
#             message = self.client.messages(message_sid).fetch()
            
#             return {
#                 'sid': message.sid,
#                 'status': message.status,
#                 'to': message.to,
#                 'from': message.from_,
#                 'body': message.body,
#                 'date_created': message.date_created,
#                 'date_sent': message.date_sent,
#                 'date_updated': message.date_updated,
#                 'error_code': message.error_code,
#                 'error_message': message.error_message,
#                 'price': message.price,
#                 'price_unit': message.price_unit
#             }
            
#         except TwilioException as e:
#             logger.error(f"Error fetching message status for {message_sid}: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"Unexpected error fetching message status: {e}")
#             return None
    
#     def get_account_balance(self) -> Optional[Dict[str, Any]]:
#         """Get Twilio account balance information"""
#         if not self.client:
#             logger.error("SMS client not initialized")
#             return None
        
#         try:
#             balance = self.client.balance.fetch()
#             return {
#                 'balance': balance.balance,
#                 'currency': balance.currency
#             }
#         except TwilioException as e:
#             logger.error(f"Error fetching account balance: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"Unexpected error fetching account balance: {e}")
#             return None
    
#     def test_sms_configuration(self) -> bool:
#         """Test SMS configuration by sending a test message to the configured from number"""
#         if not self.from_number:
#             logger.error("Cannot test SMS configuration: no from_number configured")
#             return False
        
#         test_message = f"SMS configuration test from {settings.PROJECT_NAME} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
#         message_sid = self.send_sms(self.from_number, test_message)
#         return message_sid is not None
    
#     def validate_phone_number_format(self, phone_number: str) -> bool:
#         """
#         Validate phone number format without sending SMS
        
#         Args:
#             phone_number: Phone number to validate
            
#         Returns:
#             bool: True if valid format, False otherwise
#         """
#         try:
#             self._validate_phone_number(phone_number)
#             return True
#         except ValueError:
#             return False


# # Create a global instance
# sms_service = SMSService() 