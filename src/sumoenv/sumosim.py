import os, sys, subprocess

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    from sumolib import checkBinary
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import numpy as np
from src.controllers.trafficsignalcontroller import TrafficSignalController
from src.controllers.tscfactory import tsc_factory
from src.sumoenv.vehiclegen import VehicleGen


class SumoSim:
    def __init__(self, cfg_fp, sim_len, tsc, nogui, netdata, args):
        self.cfg_fp = cfg_fp
        self.sim_len = sim_len
        self.tsc = tsc
        self.sumo_cmd = 'sumo' if nogui else 'sumo-gui' 
        self.netdata = netdata
        self.args = args
        

    def gen_sim(self):
        #create sim stuff and intersections
        #serverless_connect()
        #self.conn, self.sumo_process = self.server_connect()

        port = self.args.port
        sumoBinary = checkBinary(self.sumo_cmd)
        self.sumo_process = subprocess.Popen([sumoBinary, "-c",
                                         self.cfg_fp, "--remote-port",
                                         str(port), "--no-warnings",
                                         "--no-step-log", "--random"],
                                         stdout=None, stderr=None)

        self.conn = traci.connect(port)

        self.t = 0
        self.v_start_times = {}
        self.v_travel_times = {}
        self.vehiclegen = None
        if self.args.sim == 'double' or self.args.sim == 'single':
            self.vehiclegen = VehicleGen(self.netdata, 
                                         self.args.sim_len, 
                                         self.args.demand, 
                                         self.args.scale,
                                         self.args.mode, self.conn) 

    def run(self):
        #execute simulation for desired length
        while self.t < self.sim_len:
            #create vehicles if vehiclegen class exists
            if self.vehiclegen:
                self.vehiclegen.run()
            self.update_travel_times()
            #run all traffic signal controllers in network
            for t in self.tsc:
                self.tsc[t].run()
            self.sim_step()

    def close(self):
        self.conn.close()
        self.sumo_process.terminate()

    def update_netdata(self):
        tl_junc = self.get_traffic_lights()
        tsc = { tl:TrafficSignalController(self.conn, tl, self.args.mode, self.netdata, 2, 3)  
                     for tl in tl_junc }

        for t in tsc:
            self.netdata['inter'][t]['incoming_lanes'] = tsc[t].incoming_lanes
            self.netdata['inter'][t]['green_phases'] = tsc[t].green_phases

        all_intersections = set(self.netdata['inter'].keys())
        #only keep intersections that we want to control
        for i in all_intersections - tl_junc:
            del self.netdata['inter'][i]

        return self.netdata

    def get_traffic_lights(self):
        #find all the junctions with traffic lights
        trafficlights = self.conn.trafficlight.getIDList()
        junctions = self.conn.junction.getIDList()

        tl_juncs = set(trafficlights).intersection( set(junctions) )
        tls = []
     
        #only keep traffic lights with more than 1 green phase
        for tl in tl_juncs:
            #subscription to get traffic light phases
            self.conn.trafficlight.subscribe(tl, [traci.constants.TL_COMPLETE_DEFINITION_RYG])
            tldata = self.conn.trafficlight.getAllSubscriptionResults()
            logic = tldata[tl][traci.constants.TL_COMPLETE_DEFINITION_RYG][0]

            #for some reason this throws errors for me in SUMO 1.2
            #have to do subscription based above
            '''
            logic = self.conn.trafficlight.getCompleteRedYellowGreenDefinition(tl)[0] 
            '''
            #get only the green phases
            green_phases = [ p.state for p in logic.getPhases()
                             if 'y' not in p.state
                             and ('G' in p.state or 'g' in p.state) ]
            print(logic.getPhases())
            if len(green_phases) > 1:
                tls.append(tl)

        return set(tls) 

    def update_travel_times(self):
        for v in self.conn.simulation.getDepartedIDList():
            self.v_start_times[v] = self.t

        for v in self.conn.simulation.getArrivedIDList():
            self.v_travel_times[v] = self.t - self.v_start_times[v]
            del self.v_start_times[v]

    def sim_step(self):
        self.conn.simulationStep()
        self.t += 1
    
    def create_tsc(self):
        self.tl_junc = self.get_traffic_lights() 
        
        #create traffic signal controllers for the junctions with lights
        self.tsc = { tl: tsc_factory(self.args.tsc, tl, self.args, self.netdata, self.conn)  
                     for tl in self.tl_junc }