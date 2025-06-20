'''
Connect with the T-Watch using a USB cable.
This creates a serial port: /dev/ACM* (linux) or /dev/ttyUSB* (windows)
Unpack accelerometer data sent from T_Watch S3 running handshake firmware
The unpacked data is sent to a parse.
The parser published the parsed data using pydispatcher.
@author: matthew oppenheim
handshake project
Last update: 2025_04_03

'''
import accelerometer_data_structure as ads
import fnmatch
import logging
import math
import os
import pandas as pd
import parse_accelerometer_data
from struct import *
import struct
import serial
import sys
import time
import utilities


class Serial_Connect():
    SLEEP_TIME = 0.02 # time to sleep inbetween getting data
    BAUD = 115200

    def __init__(self, delta=100000, serial_port=None, baud=BAUD):
        if not serial_port:
            serial_port = self.find_serial_port()
        logging.debug('baud: {} port: {}'.format(baud, serial_port))
        headers = ads.acc_data_headers
        # instantiate the parser object
        self.parser = parse_accelerometer_data.Parse_accelerometer_data()
        # accelerometer sensor data will be stored in acc_scan named tuples
        self.acc_scan = ads.acc_data_structure
        try:
            serial_connection = self.serial_connect(serial_port, baud)
        except AttributeError as e:
            utilities.exit_code('no serial connection found, error code: \n{}'.format(e))
        self.get_bytes(serial_connection)


    def check_counter(self, counter):
        ''' check the counter has incremented correctly '''
        counter_delta = int(counter)-self.old_counter
        if counter_delta != 1:
            logging.debug('*** counter delta is {}'.format(counter_delta))


    def find_serial_port(self):
        ''' returns the port that the twatch  is connected to '''
        # look for a twatch connected to a /dev/ttyUSB<n> port
        ttyusbmodems = fnmatch.filter(os.listdir('/dev'), 'ttyUSB*')
        # look for a twatch connected to a /dev/ttyACM<n> port
        ttyacmmodems = fnmatch.filter(os.listdir('/dev'), 'ttyACM*')
        ttymodems = ttyusbmodems + ttyacmmodems
        twatch_port = False
        if ttymodems:
            twatch_port = '/dev/' + ttymodems[0]
            logging.debug('twatch port is {}'.format(twatch_port))
            return(twatch_port)
        # look for simulated data on /tmp/ttyV1
        ttymodems=fnmatch.filter(os.listdir('/tmp'), 'tty*')
        if ttymodems:
            twatch_port = '/tmp/'+ ttymodems[1]
            logging.info('*** using simulated data')
            logging.info('twatch port is {}'.format(twatch_port))
            return(twatch_port)
        if not twatch_port:
            utilities.exit_code('Error: no serial port connection found.')


    def get_bytes(self, serial_connection):
        '''Returns all waiting data from the open serial port.'''
        while (1):
            try:
                # don't use inWaiting() as this causes multiple calls for blank lines
                read_bytes = serial_connection.readline()
            except (IndexError, serial.serialutil.SerialException) as e:
                logging.debug(e)
            if read_bytes:
                # parser will publish complete scans of parsed data using dispatcher
                self.parser.parse_new_data(read_bytes.decode())
            # without a sleep command, this thread will suck the cpu time and bottleneck the plotting
            time.sleep(self.SLEEP_TIME)


    def serial_connect(self, serial_port, baud):
        ''' Return a serial port connection. '''
        try:
            serial_connection = serial.Serial(serial_port, baud, rtscts=True,dsrdtr=True)
            serial_connection.flushInput()
        except serial.SerialException as e:
            logging.debug('serial_connect error {}'.format(e))
            logging.debug('Could not open serial port, try\nsocat -d -d pty,raw,echo=0,link=/tmp/ttyV0 pty,raw,echo=0,link=/tmp/ttyV1')
            return None
        logging.debug('Serial port {} set up with baud {}'.format(serial_port, baud))
        return serial_connection


    def serial_write(self, message, serial_connection):
        ''' write data over serial port '''
        serial_connection.write(message)
        serial_connection.flush()


if __name__ == '__main__':
    t_watch = Serial_Connect()

