import random, os, sys
import numpy as np
from itertools import cycle
from collections import deque
from loguru import logger
import json

from src.controllers.trafficsignalcontroller import TrafficSignalController
from src.datastream.mqttclient import MQTTClient
import paho.mqtt.client as mqtt

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci

class DataStreamTSC(TrafficSignalController):
    def __init__(self, conn, tsc_id, mode, netdata, red_t, yellow_t, g_min, mqtt_host, mqtt_port):
        super().__init__(conn, tsc_id, mode, netdata, red_t, yellow_t)
        self.yellow_t = yellow_t
        self.red_t = red_t
        #for keeping track of vehicle counts for websters calc
        self.data = None
        #for determining next phase
        self.cycle = self.get_phase_cycle()
        self.green_phase_duration = { g:g_min for g in self.green_phases}
        # self.phase_deque = deque()

        #kafka client
        self.subscribed_topic = tsc_id+'_action'
        self.client = MQTTClient(id=tsc_id, host=mqtt_host, 
                                 port=mqtt_port, 
                                 on_message=self.on_message,
                                 setup_topics=[self.subscribed_topic])

        print(self.green_phases)

    def next_phase(self):
        return next(self.cycle)
        """
        if len(self.phase_deque) == 0:
            next_phase = self.get_next_phase()
            phases = self.get_intermediate_phases(self.phase, next_phase)
            self.phase_deque.extend(phases+[next_phase])
        return self.phase_deque.popleft()
        """

    def next_phase_duration(self):
        if self.phase in self.green_phases:
            return self.green_phase_duration[self.phase]
        elif 'y' in self.phase:
            return self.yellow_t
        else:
            return self.red_t

    def update(self, data):
        self.data = data 
        self.client.send(self.id, 'test')

    # utils
    def get_phase_cycle(self):
        phase_cycle = []
        greens = self.green_phases
        next_greens = self.green_phases[1:] + [self.green_phases[0]]
        for g, next_g in zip(greens, next_greens):
            phases = self.get_intermediate_phases(g, next_g)
            phase_cycle.append(g)
            phase_cycle.extend(phases)
        return cycle(phase_cycle)

    #mqtt client call back functions
    def on_message(self, client, userdata, msg):
        #logger.info(self.id+":     "+str(msg))
        if msg.topic == self.subscribed_topic:
            # need to check message timestamp
            self.get_phase_duration(msg.topic, str(msg.payload))

    def get_phase_duration(self, topic, msg):
        if topic != self.id:
            return
        logger.info(self.id+":    "+msg)
        result = json.loads(msg)
        if self.check_duration(result):
            self.green_phase_duration = result
        return

    def check_duration(self, phase_duration_dict):
        for g in self.green_phases:
            if g not in phase_duration_dict.keys():
                return False
        return True
    

    """
    def get_next_phase(self):
        #find the next green phase
        #with vehicles in approaching lanes
        i = 0
        while i <= len(self.green_phases):
            phase = next(self.cycle)
            if not self.phase_lanes_empty(phase):
                return phase
            i += 1
        ##if no vehicles approaching intersection
        #default to all red
        phase = self.all_red
        return phase 
    """