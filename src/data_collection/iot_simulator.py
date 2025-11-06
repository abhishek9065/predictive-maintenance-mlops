"""
IoT Sensor Data Simulator
Simulates real-time sensor data from industrial equipment for testing purposes.
"""

import json
import time
import random
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import yaml


class IoTSensorSimulator:
    """Simulates IoT sensor data from industrial equipment."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the simulator with configuration."""
        self.config = self._load_config(config_path)
        self.equipment_id = "PUMP_001"
        self.data_output_path = Path("data/raw")
        self.data_output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize sensor baseline values
        self.baseline = {
            "temperature": 60.0,
            "vibration": 5.0,
            "pressure": 100.0,
            "current": 25.0,
            "rpm": 2000.0
        }
        
        # Degradation parameters (simulates equipment wear)
        self.degradation_rate = {
            "temperature": 0.01,
            "vibration": 0.005,
            "pressure": -0.005,
            "current": 0.008,
            "rpm": -0.5
        }
        
        self.operating_hours = 0
        self.last_maintenance = datetime.now()
        self.is_failing = False
        self.failure_countdown = random.randint(1000, 2000)  # Time steps until failure
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}. Using defaults.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration."""
        return {
            'data': {
                'sensors': [
                    {'name': 'temperature', 'unit': 'celsius', 'normal_range': [20, 80], 'critical_threshold': 90},
                    {'name': 'vibration', 'unit': 'mm/s', 'normal_range': [0, 10], 'critical_threshold': 15},
                    {'name': 'pressure', 'unit': 'psi', 'normal_range': [80, 120], 'critical_threshold': 140},
                    {'name': 'current', 'unit': 'ampere', 'normal_range': [0, 50], 'critical_threshold': 60},
                    {'name': 'rpm', 'unit': 'revolutions_per_minute', 'normal_range': [1000, 3000], 'critical_threshold': 3500}
                ]
            }
        }
    
    def generate_sensor_reading(self, sensor_name: str, add_noise: bool = True) -> float:
        """Generate a single sensor reading with optional noise."""
        base_value = self.baseline[sensor_name]
        degradation = self.degradation_rate[sensor_name] * self.operating_hours
        
        # Add gradual degradation
        value = base_value + degradation
        
        # Simulate approaching failure
        if self.operating_hours > self.failure_countdown:
            failure_factor = (self.operating_hours - self.failure_countdown) / 100
            value += failure_factor * abs(degradation) * 10
        
        # Add random noise
        if add_noise:
            noise = np.random.normal(0, abs(base_value) * 0.02)
            value += noise
        
        # Ensure non-negative values
        return max(0, value)
    
    def generate_data_point(self) -> Dict:
        """Generate a complete data point with all sensor readings."""
        timestamp = datetime.now()
        
        data_point = {
            "equipment_id": self.equipment_id,
            "timestamp": timestamp.isoformat(),
            "operating_hours": self.operating_hours,
            "time_since_maintenance": (timestamp - self.last_maintenance).total_seconds() / 3600,
            "sensors": {}
        }
        
        # Generate readings for all sensors
        for sensor_name in self.baseline.keys():
            data_point["sensors"][sensor_name] = {
                "value": round(self.generate_sensor_reading(sensor_name), 2),
                "unit": self._get_sensor_unit(sensor_name)
            }
        
        # Determine equipment status
        data_point["status"] = self._determine_status(data_point["sensors"])
        data_point["is_failing"] = self.operating_hours > self.failure_countdown
        
        self.operating_hours += 0.1  # Increment by 0.1 hours (6 minutes)
        
        return data_point
    
    def _get_sensor_unit(self, sensor_name: str) -> str:
        """Get the unit for a sensor from configuration."""
        sensors = self.config.get('data', {}).get('sensors', [])
        for sensor in sensors:
            if sensor['name'] == sensor_name:
                return sensor['unit']
        return "unknown"
    
    def _determine_status(self, sensors: Dict) -> str:
        """Determine equipment status based on sensor readings."""
        critical_count = 0
        warning_count = 0
        
        sensor_configs = {s['name']: s for s in self.config.get('data', {}).get('sensors', [])}
        
        for sensor_name, reading in sensors.items():
            if sensor_name in sensor_configs:
                config = sensor_configs[sensor_name]
                value = reading['value']
                
                if value > config['critical_threshold']:
                    critical_count += 1
                elif value > config['normal_range'][1]:
                    warning_count += 1
        
        if critical_count > 0:
            return "critical"
        elif warning_count > 1:
            return "warning"
        else:
            return "normal"
    
    def simulate_maintenance(self):
        """Reset equipment to post-maintenance state."""
        print("Performing maintenance reset...")
        self.operating_hours = 0
        self.last_maintenance = datetime.now()
        self.failure_countdown = random.randint(1000, 2000)
    
    def stream_data(self, duration_minutes: int = 60, interval_seconds: int = 10, save_to_file: bool = True):
        """
        Stream sensor data for a specified duration.
        
        Args:
            duration_minutes: How long to stream data
            interval_seconds: Time between readings
            save_to_file: Whether to save data to file
        """
        print(f"Starting data stream for {duration_minutes} minutes...")
        print(f"Equipment ID: {self.equipment_id}")
        print(f"Sampling interval: {interval_seconds} seconds\n")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        data_buffer = []
        
        try:
            while datetime.now() < end_time:
                # Generate data point
                data_point = self.generate_data_point()
                data_buffer.append(data_point)
                
                # Print status
                status = data_point["status"]
                print(f"[{data_point['timestamp']}] Status: {status.upper()} | "
                      f"Temp: {data_point['sensors']['temperature']['value']}°C | "
                      f"Vibration: {data_point['sensors']['vibration']['value']} mm/s | "
                      f"Hours: {data_point['operating_hours']:.1f}")
                
                # Save to file periodically
                if save_to_file and len(data_buffer) >= 10:
                    self._save_data(data_buffer)
                    data_buffer = []
                
                # Simulate maintenance if critical status persists
                if status == "critical" and random.random() > 0.95:
                    self.simulate_maintenance()
                
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("\n\nData stream interrupted by user.")
        
        finally:
            # Save remaining data
            if save_to_file and data_buffer:
                self._save_data(data_buffer)
            
            print(f"\nData stream completed. Total operating hours: {self.operating_hours:.1f}")
    
    def _save_data(self, data_points: List[Dict]):
        """Save data points to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_output_path / f"sensor_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data_points, f, indent=2)
        
        print(f"  -> Saved {len(data_points)} data points to {filename}")
    
    def generate_historical_data(self, num_samples: int = 10000, failure_rate: float = 0.05):
        """
        Generate historical sensor data for training.
        
        Args:
            num_samples: Number of data points to generate
            failure_rate: Proportion of data that represents failing equipment
        """
        print(f"Generating {num_samples} historical data points...")
        
        data_points = []
        num_failures = int(num_samples * failure_rate)
        
        for i in range(num_samples):
            # Reset equipment periodically
            if i % 1500 == 0 and i > 0:
                self.simulate_maintenance()
            
            # Force failure scenario for some samples
            if i >= (num_samples - num_failures):
                self.operating_hours = self.failure_countdown + random.randint(50, 200)
            
            data_point = self.generate_data_point()
            data_points.append(data_point)
            
            if (i + 1) % 1000 == 0:
                print(f"  Generated {i + 1}/{num_samples} samples...")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_output_path / f"historical_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data_points, f, indent=2)
        
        print(f"Historical data saved to {filename}")
        print(f"  Normal samples: {num_samples - num_failures}")
        print(f"  Failure samples: {num_failures}")
        
        return data_points


def main():
    """Main function to run the simulator."""
    simulator = IoTSensorSimulator()
    
    # Generate historical training data
    print("=" * 60)
    print("GENERATING HISTORICAL DATA FOR TRAINING")
    print("=" * 60)
    simulator.generate_historical_data(num_samples=5000, failure_rate=0.1)
    
    # Reset for real-time simulation
    simulator = IoTSensorSimulator()
    
    print("\n" + "=" * 60)
    print("STARTING REAL-TIME DATA STREAM")
    print("=" * 60)
    
    # Stream real-time data
    simulator.stream_data(duration_minutes=30, interval_seconds=5)


if __name__ == "__main__":
    main()
