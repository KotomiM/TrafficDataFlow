from src.controllers.websterstsc import WebstersTSC
from src.controllers.sotltsc import SOTLTSC
from src.controllers.maxpressuretsc import MaxPressureTSC
from src.controllers.datastreamtsc import DataStreamTSC

def tsc_factory(tsc_type, tl, args, netdata, conn):
    if tsc_type == 'websters':
        return WebstersTSC(conn, tl, args.mode, netdata, args.r, args.y,
                           args.g_min, args.c_min,
                           args.c_max, args.sat_flow,
                           args.update_freq)
    elif tsc_type == 'sotl':
        return SOTLTSC(conn, tl, args.mode, netdata, args.r, args.y,
                       args.g_min, args.theta, args.omega,
                       args.mu )
    elif tsc_type == 'maxpressure':
        return MaxPressureTSC(conn, tl, args.mode, netdata, args.r, args.y,
                              args.g_min )
    elif tsc_type == 'datastream':
        return DataStreamTSC(conn, tl, args.mode, netdata, args.r, args.y, 
                             args.g_min, args.mqtt_host, args.mqtt_port)
    else:
        #raise not found exceptions
        assert 0, 'Supplied traffic signal control argument type '+str(tsc_type)+' does not exist.'
