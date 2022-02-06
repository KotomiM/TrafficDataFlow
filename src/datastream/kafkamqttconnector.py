from kafka import KafkaProducer
#from kafka import KafkaConsumer
import paho.mqtt.client as mqtt
from loguru import logger
from src.datastream.mqttclient import MQTTClient


class KafkaMQTTConnector:
    def __init__(self, mqtt_host, mqtt_port, mqtt_state_topics, bootstrap_servers=None):
        self.name = "KafkaMQTTConnector"
        bootstrap_servers = ["localhost:9092"]
        self.kafka_producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        self.mqtt_state_toipcs = mqtt_state_topics
        self.mqtt_client = MQTTClient(self.name, mqtt_host, mqtt_port, self.on_message, mqtt_state_topics)

    def on_message(self, client, userdata, msg):
        if msg.topic in self.mqtt_state_toipcs:
            logger.info("test mqtt connector: " + msg.topic + " : " + str(msg.payload))
            #self.publish_kafka_message(msg.topic, str(msg.payload))
            
    def publish_kafka_message(self, topic, value):
        # key_bytes = bytes(key, encoding='utf-8')
        #value_bytes = bytes(value, encoding='utf-8')
        self.kafka_producer.send(topic, value=value.encode('utf-8'))
        self.kafka_producer.flush()
        # logger.info("sent kafka message: " + value)