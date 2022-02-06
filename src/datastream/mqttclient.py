import paho.mqtt.client as mqtt
from loguru import logger

class MQTTClient:
    def __init__(self, id, host, port, on_message, setup_topics=[]):
        self.id = id
        self.client = self._setup_mqtt(host, port, on_message)
        self.latest_msg = ''

        self.received = False
        if len(setup_topics) != 0:
            for topic in setup_topics:
                self.client.subscribe(topic)
    
    def subscribe(self, topic):
        self.client.subscribe(topic)
    
    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)

    def send(self, topic, message):
        self.client.publish(topic, message)

    def _setup_mqtt(self, host, port, on_message):
        def on_connect(client, userdata, flags, rc):
            client.subscribe("$SYS/#")

        #def on_publish(client, userdata, mid):
        #    pass

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        #client.on_publish = on_publish

        client.connect(host, port)
        client.loop_start()
        return client