'''
pyzmq pair socket handler
Created on 1 Nov 2016
using qt timer and polling instead of the tornado loop in zmq
@author: matthew oppenheim
'''

import accelerometer_data_structure as ads
import json
import logging
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import zmq
import sys
import time

class ZmqPair():
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        port = '5556'
        self.socket, context = self.create_socket(port)
        
    def create_socket(self, port):
        ''' return the zmq.PAIR socket and context  '''
        context = zmq.Context()
        socket = context.socket(zmq.PAIR)
        socket.connect('tcp://localhost:%s' % ads.ZMQ_PORT) 
        socket.setsockopt(zmq.LINGER, 0)
        logging.info('twatch created zmq.PAIR socket: {}'.format(socket))
        return socket, context
    
    def send_message(self, text):
        ''' send message to socket '''
        self.socket.send_string(text)
        logging.info('twatch sent {} to socket'.format(text))
        
    def get_message(self):
        ''' get json message through socket and return '''
        msg = None
        try:
            msg = json.loads(self.socket.recv(flags=zmq.NOBLOCK).decode())
            # need another json.loads to parse string into dictionary
            msg = json.loads(msg)
            logging.info('received message through zmq {}'.format(msg))
            self.send_message('twatch received message')
            return msg
        # raises zmq.errror.Again if no message
        except zmq.error.Again as e:
            pass
 