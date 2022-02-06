from kafka import KafkaProducer

class Producer:
    def __init__(self, id, bootstrap_servers):
        self.id = id
        self.kafka_producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        
    def publish_kafka_message(self, topic, value):
        self.kafka_producer.send(topic, value)
        self.kafka_producer.flush()