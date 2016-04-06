#!/usr/bin/env python

import time
import os
import sys
from pymavlink import mavutil
from pubnub import Pubnub

def delay():
    global last
    now = time.time()
    if ((now - last) > mindelay):
        last = now
        return False
    else:
        return True

def loop_messages(m):
    '''loop through mavlink messages'''
    print("forwardpubnub: Started messages loop")
    while True:
        msg = m.recv_match(blocking=True)
        if not msg:
            return
        if msg.get_type() == 'ATTITUDE':
            if delay():
                continue
            if debug:
                print("forwardpubnub %f: %f,%f,%f" % (last * 1000, msg.pitch, msg.yaw, msg.roll))
            else:
                pubnub.publish(channel='gyroscope', message=[last * 1000, msg.pitch, msg.yaw, msg.roll])
            return

def killWithFireCallback(message, channel):
    if (channel == 'gyroscope'):
        if (message == 'kill'):
            print("forwardpubnub: Received kill signal!")

            if (not master.target_system) or (not master.target_component):
                print("forwardpubnub: No target sytem/component yet. Will wait for heartbeat.")
                master.wait_heartbeat()

            # https://github.com/mavlink/mavlink/blob/master/message_definitions/v1.0/common.xml
            # master.arducopter_disarm()
            master.mav.command_long_send(
                target_system,  # target_system
                target_component, # target_component
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, # command
                0, # confirmation
                0, # param1
                0, # param2
                0, # param3
                0, # param4
                0, # param5
                0, # param6
                0) # param7
        elif (message == 'faster'):
            if (mindelay - 0.1) > 0:
                mindelay = mindelay - 0.1
            else:
                print("forwardpubnub: 0.1 is fastest")
            pubnub.publish(channel='speed', message=mindelay)
        elif (message == 'slower'):
            if (mindelay + 0.1) < 10:
                mindelay = mindelay + 0.1
            else:
                print("forwardpubnub: 10s is slowest")
            pubnub.publish(channel='speed', message=mindelay)

#
# MAIN
#

print("forwardpubnub: Initialize module")

debug=False
mindelay = 5.0
last = time.time()
device='/dev/ttyMFD1'
baudrate='921600'

# Pubnub stuff
pubnubPublishKey=os.getenv('PUBNUB_PUBLISH_KEY', '')
pubnubSubscribeKey=os.getenv('PUBNUB_SUBSCRIBE_KEY', '')
if (not pubnubPublishKey) or (not pubnubSubscribeKey):
    print("forwardpubnub: PUBNUB_PUBLISH_KEY and/or PUBNUB_SUBSCRIBE_KEY not available. Please set all these env variables.")
    sys.exit(1)
pubnub = Pubnub(publish_key=pubnubPublishKey, subscribe_key=pubnubSubscribeKey)
pubnub.subscribe(channels='gyroscope', callback=killWithFireCallback)

# Open serial
master = mavutil.mavlink_connection(device, baudrate)

print("forwardpubnub: Module initialized")

# Loop
loop_messages(master)

# Close serial
master.close()

# Force exit all threads too
os._exit(0)