#!/usr/bin/env python
# -*- mode: python; coding: utf-8; fill-column: 80; -*-
#
# sim-fwall.py
# Created by Balakrishnan Chandrasekaran on 2015-08-01 00:55 -0500.
#

"""
sim-fwall.py
"""

__author__  = 'Balakrishnan Chandrasekaran <balac@cs.duke.edu>'
__version__ = '1.0'
__license__ = 'MIT'

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import LinearTopo, Topo
import os
import random
import sys
import time

# Random number generator seed
# For repeatable random sequences
RNG_SEED = 10302015
# For truly random sequences
# RNG_SEED = long(time.time())

# Number of events to generate
E = 350

# Time in seconds between the events
T = 0.01

# Controller name and IP
CTRLR_NAME = 'galvatron.cs.duke.edu'
CTRLR_IP = '152.3.144.152'

class CustomTopo(Topo):
    """Custom topology for testing route manager application.

        h1 h2    h3 h4
        |  |      |  |
	s1-s2----s3-s4
         (in)    (out)
    """
    def __init__(self, fm='secure'):
        Topo.__init__(self)

        # Add hosts/switches
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
	s1 = self.addSwitch('s1', protocols='OpenFlow13', failMode=fm)
	s2 = self.addSwitch('s2', protocols='OpenFlow13', failMode=fm)
	s3 = self.addSwitch('s3', protocols='OpenFlow13', failMode=fm)
	s4 = self.addSwitch('s4', protocols='OpenFlow13', failMode=fm)

        # Connect hosts to switches
        self.addLink(h1, s1)
	self.addLink(h2, s2)
        self.addLink(h3, s3)
	self.addLink(h4, s4)

        # Connect switches
	self.addLink(s1, s2, delay='1ms')
	self.addLink(s2, s3, delay='1ms')
	self.addLink(s3, s4, delay='1ms')


def setup(ctrlr_name, ctrlr_ip, fm):
    """Setup the topology and configuration.
    """
    topo = CustomTopo(fm)
    net = Mininet(topo,
                  controller=RemoteController,
                  link=TCLink,
                  autoSetMacs=True,
                  autoStaticArp=False,
                  build=False)
    remote = RemoteController(ctrlr_name, ip=ctrlr_ip)
    net.addController(remote)
    net.build()
    return net

def get_sname(i):
    """Get name of switch.
    """
    return "s%d" % (i)

def get_hname(i):
    """Get name of host.
    """
    return "h%d" % (i)

def run_exp(net, num_events, pause_time):
    """Run experiment to generate link up/down events.
    """
    out_path = '/tmp'
    # CLI(net)

    # Wait till routes are populated.
    try:
        print('#> waiting till network is setup ...')
        time.sleep(10)
        print('#> network is setup')
    except KeyboardInterrupt as e:
        raise e

    # Destinations (pong)
    dst_ids = (4, 3)
    dsts = map(lambda h: net.get("h%d" % (h)), dst_ids)
    for dst in dsts:
        print("#> tcppong @ %s" % (dst.IP()))

    # Sources (ping)
    src_ids = (1, 2)
    srcs = map(lambda h: net.get("h%d" % (h)), src_ids)
    for src in srcs:
        print("#> tcpping @ %s" % (src.IP()))

    # raw_input('> press any key to start!')
    CLI(net)
    try:
        for dst in dsts:
            # Run pong in the background
            pong_cmd = "./ext/tcppong.py -m %s &" % (dst.IP())
            dst.cmd(pong_cmd)
            print("#> " + pong_cmd)
        
        i = 0
        for src, dst in zip(srcs, dsts):
            out_file = os.path.sep.join((out_path,
                                         "h%d-to-h%d-log.txt" % (
                                             src_ids[i], dst_ids[i])))
            # Run ping
            if src.IP() == '10.0.0.2':
                ping_cmd = "./ext/tcpping.py -w 30 -m %s %s &" % (dst.IP(), out_file)
            else:
                ping_cmd = "./ext/tcpping.py -m %s %s &" % (dst.IP(), out_file)
            src.cmd(ping_cmd)
            print("#> " + ping_cmd)
            i += 1

        # Wait for flows to proceed a bit.
        try:
            d = 90
            print('#> allow flows to proceed for %d seconds.' % (d))
            time.sleep(d)
            print('#> tearing down experiment ...')
        except KeyboardInterrupt as e:
            raise e

        # CLI(net)
    except Exception as e:
        sys.stderr.write("Error: %s\n" % (e))
    finally:
        for src in srcs:
            try:
                src.cmd('kill %./ext/tcpping.py')
            except:
                continue
        for dst in dsts:
            try:
                dst.cmd('kill %./ext/tcppong.py')
            except:
                continue

if __name__ == '__main__':
    setLogLevel('info')
    n = None
    try:
        n = setup(CTRLR_NAME, CTRLR_IP, 'secure')
        n.start()
        run_exp(n, E, T)
    except Exception as e:
        import sys
        sys.stderr.write("Error: %s\n" % str(e))
    finally:
        raw_input('> press any key to quit!')
        if n:
            n.stop()
