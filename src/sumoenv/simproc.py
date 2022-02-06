import sys, os, time
from multiprocessing import *

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci

from src.sumoenv.sumosim import SumoSim
from src.sumoenv.helper_funcs import check_and_make_dir, get_time_now, write_to_log

class SimProc(Process):
    def __init__(self, args, barrier, netdata):
        Process.__init__(self)
        self.args = args
        self.barrier = barrier
        self.netdata = netdata
        self.sim = SumoSim(args.cfg_fp, args.sim_len, args.tsc, args.nogui, netdata, args)
        self.initial = True 

    def run(self):
        print('sim proc waiting at barrier ---------')
        write_to_log('ACTOR # WAITING AT SYNC WEIGHTS BARRIER...')
        self.barrier.wait()
        write_to_log('ACTOR # BROKEN SYNC BARRIER...')
        #barrier
        
        start_t = time.time()
        self.sim.gen_sim()
        self.sim.create_tsc()
        self.sim.run()
        print('sim finished in '+str(time.time()-start_t)+' on proc ')
        write_to_log('ACTOR # FINISHED SIM...')

        self.sim.close()

        print('------------------\nFinished on sim process Closing\n---------------')
        
