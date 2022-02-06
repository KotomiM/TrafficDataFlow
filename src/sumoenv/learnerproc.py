import time, os
from multiprocessing import *
import numpy as np

from src.sumoenv.helper_funcs import write_line_to_file, check_and_make_dir, get_time_now, write_to_log

class LearnerProc(Process):
    def __init__(self, idx, args, barrier, netdata, agent_ids):
        Process.__init__(self)
        self.idx = idx
        self.args = args
        self.barrier = barrier
        self.netdata = netdata
        self.agent_ids = agent_ids
        self.save_t = 0
        self.replay_fp =  self.args.save_replay+'/'+self.args.tsc+'/'

    def run(self):

        #wait for all procs to sync weights
        print('learner waiting at barrier ------------')
        write_to_log(' LEARNER #'+str(self.idx)+' FINISHED SENDING WEIGHTS, WAITING AT BARRIER...')
        self.barrier.wait()
        write_to_log(' LEARNER #'+str(self.idx)+' GENERATING AGENTS...')

        if self.args.load_replay:
            self.load_replays()

        #create agents
        agents = self.gen_agents(neural_networks)

        print('learner proc '+str(self.idx)+' waiting at offset barrier------------')
        write_to_log(' LEARNER #'+str(self.idx)+' FINISHED GEN AGENTS, WAITING AT OFFSET BARRIER...')
        self.barrier.wait()
        write_to_log(' LEARNER #'+str(self.idx)+' BROKEN OFFSET BARRIER...')
        print('learner proc '+str(self.idx)+' broken offset barrier ------------')

        self.save_t = time.time()
        othert = time.time()
        """
        #keep looping until all agents have
        #achieved sufficient batch updates
        while not self.finished_learning(self.agent_ids):
            for tsc in self.agent_ids:
                #wait until exp replay buffer full
                if len(self.exp_replay[tsc]) >= self.args.nreplay:
                    #reset the number of experiences once when the 
                    #exp replay is filled for the first time
                    if self.rl_stats[tsc]['updates'] == 0:
                        if self.args.save:
                            self.save_replays()
                        print(tsc+' exp replay full, beginning batch updates********')
                        #write_to_log(' LEARNER #'+str(self.idx)+' START LEARNING '+str(tsc))
                        self.rl_stats[tsc]['n_exp'] = len(self.exp_replay[tsc])
                    if self.rl_stats[tsc]['updates'] < self.args.updates and self.rl_stats[tsc]['n_exp'] > 0: 
                        for i in range(min(self.rl_stats[tsc]['n_exp'], 4)):
                           agents[tsc].train_batch(self.args.target_freq)
                        agents[tsc].clip_exp_replay()

        """
        while not self.finished_learning(self.agent_ids):
            t = time.time()
            if t - othert > 90:
                othert = t
                n_replay = [str(len(self.exp_replay[i])) for i in self.agent_ids]
                updates = [str(self.rl_stats[i]['updates']) for i in self.agent_ids]
                nexp = [str(self.rl_stats[i]['n_exp']) for i in self.agent_ids]
                write_to_log(' LEARNER #'+str(self.idx)+'\n'+str(self.agent_ids)+'\n'+str(nexp)+'\n'+str(n_replay)+'\n'+str(updates))                           


            #save weights periodically
            if self.args.save:
                if self.time_to_save():
                    self.save_weights(neural_networks)

                    #write agent training progress
                    #only on one learner
                    if self.idx == 0:
                        self.write_progress()
        write_to_log(' LEARNER #'+str(self.idx)+' FINISHED TRAINING LOOP ===========')

        if self.idx == 0:
            #if other agents arent finished learning
            #keep updating progress
            while not self.finished_learning(self.tsc_ids):
                if self.time_to_save():
                    self.write_progress()
