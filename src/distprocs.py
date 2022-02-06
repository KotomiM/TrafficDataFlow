import sys, os, subprocess, time
from multiprocessing import *
import numpy as np

from src.sumoenv.sumosim import SumoSim
from src.sumoenv.networkdata import NetworkData
from src.sumoenv.simproc import SimProc
from src.sumoenv.learnerproc import LearnerProc
from src.datastream.kafkamqttconnector import KafkaMQTTConnector

# from src.agents.learnerproc import LearnerProc

def get_sim(sim_str):             
    if sim_str == 'single':                                       
        cfg_fp = 'networks/single.sumocfg'                         
        net_fp = 'networks/single.net.xml'                           
    elif sim_str == 'double':                                       
        cfg_fp = 'networks/double.sumocfg'                         
        net_fp = 'networks/double.net.xml'                           
    return cfg_fp, net_fp   


class DistProcs:
    def __init__(self, args, tsc, mode):
        self.args = args
        # rl_tsc = ['ddpg', 'dqn']
        # traditional_tsc = ['websters', 'maxpressure', 'sotl', 'uniform']

        #depending on mode, different hyper param checks

        if mode == 'train':
            #ensure we have at least one learner
            if args.l < 1:
                args.l = 1
        elif mode == 'test':
            #no learners necessary for testing
            if args.l > 0:
                args.l = 0

        #if sim arg provided, use to get cfg and netfp
        #otherwise, continue with args default
        if args.sim:
            args.cfg_fp, args.net_fp = get_sim(args.sim)

        #barrier = Barrier(1+args.l)
        barrier = Barrier(1)

        nd = NetworkData(args.net_fp)
        netdata = nd.get_net_data()

        #create a dummy sim to get tsc data for creating nn
        #print('creating dummy sim for netdata...')
        sim = SumoSim(args.cfg_fp, args.sim_len, args.tsc, True, netdata, args)
        sim.gen_sim()
        netdata = sim.update_netdata()
        sim.close()
        #print('...finished with dummy sim')

        #get intersection ids
        tsc_ids = netdata['inter'].keys()
        print(tsc_ids)
    
        #create sumo sim procs to generate experiences
        sim_procs = [ SimProc(args, barrier, netdata) ]
        learner_procs = []
        """
        #create learner procs which ar·e assigned tsc/rl agents
        #to compute neural net updates for
        if args.l > 0:
            learner_agents = self.assign_learner_agents( tsc_ids, args.l)
            print('===========LEARNER AGENTS')
            for l in learner_agents:
                print('============== '+str(l))
            learner_procs = [ LearnerProc(i, args, barrier, netdata, learner_agents[i]) for i in range(args.l)]
        else:
            learner_procs = []
        """
        self.procs = sim_procs + learner_procs
        self.stream_connector = KafkaMQTTConnector(args.mqtt_host, args.mqtt_port, list(tsc_ids))

    def run(self):
        print('Starting up all processes...')
        ###start everything   
        for p in self.procs:
            p.start()
                              
        ###join when finished
        for p in self.procs:
            p.join()

        print('...finishing all processes')

    def assign_learner_agents(self, agents, n_learners):
        learner_agents = [ [] for _ in range(n_learners)]
        for agent, i in zip(agents, range(len(agents))):
            learner_agents[i%n_learners].append(agent)
        ##list of lists, each sublit is the agents a learner is responsible for
        return learner_agents
