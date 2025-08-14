import aioboto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.core.logger import logger


class AWSService:
    """
    A fully async class to interact with various AWS services like S3, SQS, and SNS using aioboto3.
    Located in the 'integrations' package.
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key: Optional[str] = settings.AWS_SECRET_ACCESS_KEY,
        region_name: str = settings.AWS_REGION,
        s3_bucket_name: Optional[str] = settings.AWS_S3_BUCKET_NAME,
        sqs_queue_url: Optional[str] = settings.AWS_SQS_INCOMING_EVENTS_QUEUE_URL,
    ):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.s3_bucket_name = s3_bucket_name
        self.sqs_queue_url = sqs_queue_url

        # Session configuration
        self.session_params = {
            "region_name": self.region_name,
        }
        
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.session_params["aws_access_key_id"] = self.aws_access_key_id
            self.session_params["aws_secret_access_key"] = self.aws_secret_access_key

        self.session = None
        self._initialized = False

    async def _ensure_session(self):
        """Ensure the session is initialized (lazy initialization)"""
        if not self._initialized:
            try:
                self.session = aioboto3.Session(**self.session_params)
                self._initialized = True
                logger.info("Async AWS Service initialized successfully with aioboto3.")
            except Exception as e:
                logger.error(f"Error initializing async AWS Service: {e}")
                raise

    # --- S3 Methods ---
    async def upload_file_to_s3(
        self,  file_path: str, bucket_name: Optional[str] = None,object_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to an S3 bucket.

        :param bucket_name: S3 bucket name file to upload.
        :param file_path: Path to the file to upload.
        :param object_name: S3 object name. If not specified, file_path's base name is used.
        :return: URL of the uploaded file, or None if upload failed.
        """
        await self._ensure_session()

        upload_bucket_name = bucket_name or self.s3_bucket_name
        
        if not upload_bucket_name:
            logger.error("S3 bucket name not configured. Cannot upload file.")
            return None
            
        if object_name is None:
            object_name = file_path.split("/")[-1]
            
        try:
            async with self.session.client("s3") as s3_client:
                await s3_client.upload_file(file_path, upload_bucket_name, object_name)
                file_url = f"https://{upload_bucket_name}.s3.{self.region_name}.amazonaws.com/{object_name}"
                logger.info(
                    f"File {object_name} uploaded to S3 bucket {upload_bucket_name}. URL: {file_url}"
                )
                return file_url
        except FileNotFoundError:
            logger.error(f"The file was not found: {file_path}")
            return None
        except NoCredentialsError:
            logger.error("Credentials not available for S3 upload.")
            return None
        except ClientError as e:
            logger.error(f"S3 ClientError during upload: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during S3 upload: {e}")
            return None

    async def get_s3_file_url(
        self, object_name: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for an S3 object.

        :param object_name: S3 object name.
        :param expiration: Time in seconds for the presigned URL to remain valid.
        :return: Presigned URL string, or None if error.
        """
        await self._ensure_session()
        
        if not self.s3_bucket_name:
            logger.error("S3 bucket name not configured. Cannot get file URL.")
            return None
            
        try:
            async with self.session.client("s3") as s3_client:
                response = await s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.s3_bucket_name, "Key": object_name},
                    ExpiresIn=expiration,
                )
                logger.info(
                    f"Generated presigned URL for {object_name} in bucket {self.s3_bucket_name}"
                )
                return response
        except ClientError as e:
            logger.error(f"S3 ClientError generating presigned URL: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred generating presigned URL: {e}")
            return None

    async def copy_s3_object(
        self, 
        source_object_key: str, 
        destination_object_key: str
    ) -> Optional[str]:
        """
        Copy an S3 object to a new location.

        :param source_object_key: Source S3 object key.
        :param destination_object_key: Destination S3 object key.
        :param source_bucket: Source bucket name (optional, uses default bucket if not provided).
        :return: URL of the copied object, or None if copy failed.
        """
        await self._ensure_session()
        
        if not self.s3_bucket_name:
            logger.error("S3 bucket name not configured. Cannot copy object.")
            return None
        
        # Use source bucket if provided, otherwise use default bucket
        source_bucket_name = self.s3_bucket_name
        destination_bucket = settings.AWS_S3_PROFILE_PICTURES_BUCKET_NAME
            
        try:
            async with self.session.client("s3") as s3_client:
                # Copy object
                copy_source = {
                    'Bucket': source_bucket_name,
                    'Key': source_object_key
                }
                
                await s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=destination_bucket,
                    Key=destination_object_key
                )
                
                # Generate URL for the copied object
                file_url = f"https://{destination_bucket}.s3.{self.region_name}.amazonaws.com/{destination_object_key}"
                logger.info(
                    f"Object {source_object_key} copied to {destination_object_key} in bucket {destination_bucket}. URL: {file_url}"
                )
                return file_url
        except ClientError as e:
            logger.error(f"S3 ClientError during copy: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during S3 copy: {e}")
            return None

    # --- SQS Methods ---
    async def send_sqs_message(
        self, message_body: str, message_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Send a message to an SQS queue.

        :param message_body: The message body string.
        :param message_attributes: Optional dictionary of message attributes.
        :return: Message ID if successful, else None.
        """
        await self._ensure_session()
        
        if not self.sqs_queue_url:
            logger.error("SQS queue URL not configured. Cannot send message.")
            return None
            
        try:
            async with self.session.client("sqs") as sqs_client:
                params = {
                    "QueueUrl": self.sqs_queue_url,
                    "MessageBody": message_body,
                }
                if message_attributes:
                    params["MessageAttributes"] = message_attributes

                response = await sqs_client.send_message(**params)
                message_id = response.get("MessageId")
                logger.info(
                    f"Message sent to SQS queue {self.sqs_queue_url}. Message ID: {message_id}"
                )
                return message_id
        except ClientError as e:
            logger.error(f"SQS ClientError sending message: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred sending SQS message: {e}")
            return None

    async def receive_sqs_messages(
        self, max_number_of_messages: int = 1, wait_time_seconds: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from an SQS queue.

        :param max_number_of_messages: Maximum number of messages to retrieve.
        :param wait_time_seconds: The duration (in seconds) for which the call waits for a message to arrive.
        :return: A list of messages, or an empty list if no messages or error.
        """
        await self._ensure_session()
        
        if not self.sqs_queue_url:
            logger.error("SQS queue URL not configured. Cannot receive messages.")
            return []
            
        try:
            async with self.session.client("sqs") as sqs_client:
                response = await sqs_client.receive_message(
                    QueueUrl=self.sqs_queue_url,
                    MaxNumberOfMessages=max_number_of_messages,
                    WaitTimeSeconds=wait_time_seconds,
                    MessageAttributeNames=["All"],
                    AttributeNames=["All"],
                )
                messages = response.get("Messages", [])
                if messages:
                    logger.info(
                        f"Received {len(messages)} messages from SQS queue {self.sqs_queue_url}."
                    )
                return messages
        except ClientError as e:
            logger.error(f"SQS ClientError receiving messages: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred receiving SQS messages: {e}")
            return []

    async def delete_sqs_message(self, receipt_handle: str) -> bool:
        """
        Delete a message from an SQS queue.

        :param receipt_handle: The receipt handle of the message to delete.
        :return: True if successful, False otherwise.
        """
        await self._ensure_session()
        
        if not self.sqs_queue_url:
            logger.error("SQS queue URL not configured. Cannot delete message.")
            return False
            
        try:
            async with self.session.client("sqs") as sqs_client:
                await sqs_client.delete_message(
                    QueueUrl=self.sqs_queue_url, ReceiptHandle=receipt_handle
                )
                logger.info(
                    f"Message with receipt handle {receipt_handle} deleted from SQS queue {self.sqs_queue_url}."
                )
                return True
        except ClientError as e:
            logger.error(f"SQS ClientError deleting message: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred deleting SQS message: {e}")
            return False

    # --- SNS Methods ---
    async def publish_sns_message(
        self,
        topic_arn: str,
        message: str,
        subject: Optional[str] = None,
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Publish a message to a specific SNS topic (standard topics only).

        :param topic_arn: The ARN of the SNS topic to publish to.
        :param message: The message body string.
        :param subject: Optional subject for the message (used for email notifications).
        :param message_attributes: Optional dictionary of message attributes.
        :return: Message ID if successful, else None.
        """
        await self._ensure_session()
        
        if not topic_arn:
            logger.error("SNS Topic ARN not provided. Cannot publish message.")
            return None
            
        try:
            async with self.session.client("sns") as sns_client:
                params = {
                    "TopicArn": topic_arn,
                    "Message": message,
                }
                if subject:
                    params["Subject"] = subject
                if message_attributes:
                    params["MessageAttributes"] = message_attributes

                response = await sns_client.publish(**params)
                message_id = response.get("MessageId")
                
                logger.info(
                    f"Message published to SNS topic {topic_arn}. Message ID: {message_id}"
                )
                return message_id
        except ClientError as e:
            logger.error(f"SNS ClientError publishing message to {topic_arn}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred publishing SNS message to {topic_arn}: {e}"
            )
            return None


# Create a global instance
aws_service = AWSService() 