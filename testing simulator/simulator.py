import os
import json
import time
import random
import logging
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vehicle-simulator")

# Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX")
SIM_SPEED_FACTOR = int(os.getenv("SIM_SPEED_FACTOR"))

# Simulated Vehicles (Starting rough coordinates around Colombo, Sri Lanka)
VEHICLES = {
    "LORRY-001": {"lat": 6.9271, "lon": 79.8612},
    "LORRY-002": {"lat": 6.9350, "lon": 79.8480},
    "TRUCK-001": {"lat": 6.9100, "lon": 79.8700}
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"✅ Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        logger.error(f"❌ Connection failed with code {rc}")

def simulate_movement(vehicle_id, data):
    # Random walk: move lat/lon slightly to simulate driving
    data["lat"] += random.uniform(-0.0005, 0.0005)
    data["lon"] += random.uniform(-0.0005, 0.0005)
    
    speed = random.uniform(20, 60) # km/h
    heading = random.uniform(0, 360)
    
    payload = {
        "vehicle_id": vehicle_id,
        "lat": round(data["lat"], 6),
        "lon": round(data["lon"], 6),
        "speed": round(speed, 2),
        "heading": round(heading, 2),
        "timestamp": int(time.time() * 1000)
    }
    return payload

def run_simulator():
    logger.info("Initializing Vehicle Simulator...")
    
    # Initialize MQTT Client
    client = mqtt.Client(client_id=f"sim_vehicle_{random.randint(1000, 9999)}")
    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        
    client.on_connect = on_connect
    
    # Connect loop
    while True:
        try:
            logger.info(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            logger.warning(f"Could not connect to broker: {e}. Retrying in 5s...")
            time.sleep(5)

    client.loop_start()

    try:
        while True:
            for vehicle_id, data in VEHICLES.items():
                payload = simulate_movement(vehicle_id, data)
                
                # Format: vehicles/LORRY-001/location
                topic = f"{TOPIC_PREFIX}/{vehicle_id}/location"
                
                # QoS 1 for guaranteed delivery to EMQX
                client.publish(topic, json.dumps(payload), qos=1)
                logger.info(f"Published to {topic}: {payload}")
                
            # Sleep before next tick (adjustable via SIM_SPEED_FACTOR)
            # A real GPS might ping every 5-10 seconds.
            sleep_time = 10.0 / SIM_SPEED_FACTOR
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run_simulator()
