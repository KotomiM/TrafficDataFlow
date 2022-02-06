from kafka import KafkaConsumer

class Consumer:
    def __init__(self, id, bootstrap_servers, topics):
        self.id = id
        self.kafka_consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        self.kafka_consumer.subscribe(topics) 
        
    def run(self):
        for msg in self.kafka_consumer:
            self.manage(msg)

    def manage(self, action):
        pass