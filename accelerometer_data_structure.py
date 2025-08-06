'''
Created on 31 Dec 2015
accelerometer data structure
m: number of milliseconds since start
c: incrementing counter
acc_x: accelerometer x value
acc_y: accelerometer y value
acc_z: accelerometer z value
@author: matthew
'''

import collections
import numpy as np

AMPLITUDE = 2

DISPLAY_SENDER = 'display_sender'
DISPLAY_SIGNAL= 'display_signal'
FRAMES_PER_SECOND = 30
GESTURE_SENDER = 'gesture_sender'
GESTURE_SIGNAL = 'gesture_signal'
SHAKE_SIGNAL = 'shake_signal'
SHAKE_SENDER = 'shake_sender'
PACKER = '2shhfff2s'
ZMQ_PORT = '5556'


acc_data_structure = collections.namedtuple('acc_scan', 'millis, counter, acc_x, acc_y, acc_z')
acc_data_headers = ['millis', 'counter', 'acc_x', 'acc_y', 'acc_z']


