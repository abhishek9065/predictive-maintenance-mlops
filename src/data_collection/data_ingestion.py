"""
Data Ingestion Module
Handles real-time data collection from IoT sensors and cloud platforms.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import boto3
from azure.iot.device import IoTHubDeviceClient, Message
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Handles ingestion of sensor data from various sources."""
    
    def __init__(self, config: Dict):
        """Initialize the data ingestion pipeline."""
        self.config = config
        self.data_buffer = []
        self.buffer_size = 100
        self.output_path = Path(config.get('data', {}).get('raw_data_path', 'data/raw'))
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def ingest_from_iot_hub(self, connection_string: str):
        """Ingest data from Azure IoT Hub."""
        logger.info("Connecting to Azure IoT Hub...")
        
        try:
            client = IoTHubDeviceClient.create_from_connection_string(connection_string)
            client.connect()
            logger.info("Connected to IoT Hub successfully")
            
            # This would typically be in a separate receiver
            # For demonstration, showing the structure
            return client
        
        except Exception as e:
            logger.error(f"Failed to connect to IoT Hub: {e}")
            raise
    
    def ingest_from_aws_iot(self, thing_name: str, endpoint: str):
        """Ingest data from AWS IoT Core."""
        logger.info("Connecting to AWS IoT Core...")
        
        try:
            iot_client = boto3.client('iot-data', region_name=self.config['cloud']['aws']['region'])
            
            # Subscribe to shadow updates
            response = iot_client.get_thing_shadow(thingName=thing_name)
            shadow = json.loads(response['payload'].read())
            
            logger.info(f"Connected to AWS IoT thing: {thing_name}")
            return iot_client
        
        except Exception as e:
            logger.error(f"Failed to connect to AWS IoT: {e}")
            raise
    
    def ingest_batch_data(self, data_points: List[Dict]):
        """Ingest a batch of data points."""
        self.data_buffer.extend(data_points)
        logger.info(f"Ingested {len(data_points)} data points. Buffer size: {len(self.data_buffer)}")
        
        # Flush buffer if it's full
        if len(self.data_buffer) >= self.buffer_size:
            self.flush_buffer()
    
    def flush_buffer(self):
        """Flush data buffer to storage."""
        if not self.data_buffer:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_path / f"ingested_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.data_buffer, f, indent=2)
        
        logger.info(f"Flushed {len(self.data_buffer)} data points to {filename}")
        self.data_buffer = []
    
    def store_to_s3(self, bucket_name: str, data: Dict):
        """Store data to AWS S3."""
        try:
            s3_client = boto3.client('s3', region_name=self.config['cloud']['aws']['region'])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"raw-data/{timestamp}.json"
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=json.dumps(data)
            )
            
            logger.info(f"Data stored to S3: s3://{bucket_name}/{key}")
        
        except Exception as e:
            logger.error(f"Failed to store data to S3: {e}")
            raise
    
    def validate_data_point(self, data_point: Dict) -> bool:
        """Validate a single data point."""
        required_fields = ['equipment_id', 'timestamp', 'sensors']
        
        for field in required_fields:
            if field not in data_point:
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True


class StreamProcessor:
    """Process streaming data in real-time."""
    
    def __init__(self, ingestion_pipeline: DataIngestionPipeline):
        """Initialize the stream processor."""
        self.pipeline = ingestion_pipeline
        self.processed_count = 0
    
    def process_message(self, message: Dict):
        """Process a single message from the stream."""
        try:
            # Validate message
            if not self.pipeline.validate_data_point(message):
                logger.warning("Invalid message received")
                return
            
            # Add metadata
            message['ingestion_timestamp'] = datetime.now().isoformat()
            message['processed'] = False
            
            # Ingest to pipeline
            self.pipeline.ingest_batch_data([message])
            self.processed_count += 1
            
            if self.processed_count % 100 == 0:
                logger.info(f"Processed {self.processed_count} messages")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def start_stream(self, source: str = "simulator"):
        """Start processing the data stream."""
        logger.info(f"Starting stream processor for source: {source}")
        # Implementation would depend on the actual streaming source
        pass


def main():
    """Main function for testing data ingestion."""
    config = {
        'data': {
            'raw_data_path': 'data/raw'
        },
        'cloud': {
            'aws': {
                'region': 'us-east-1',
                's3_bucket': 'predictive-maintenance-data'
            }
        }
    }
    
    pipeline = DataIngestionPipeline(config)
    processor = StreamProcessor(pipeline)
    
    # Test with sample data
    sample_data = {
        'equipment_id': 'PUMP_001',
        'timestamp': datetime.now().isoformat(),
        'sensors': {
            'temperature': {'value': 65.5, 'unit': 'celsius'},
            'vibration': {'value': 5.2, 'unit': 'mm/s'}
        }
    }
    
    processor.process_message(sample_data)
    pipeline.flush_buffer()
    
    logger.info("Data ingestion test completed")


if __name__ == "__main__":
    main()
