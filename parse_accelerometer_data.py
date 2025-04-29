'''
Parse accelerometer data from t_watch.

Part of the handshake project: mattoppenheim.com/handshake.
Sensor data example:

[DEBUG] accelerometer.cpp L.39 log_acc : ST m:  10041 c:  57 x:  228 y:  270 z:  -369 EN 

Parses data into a named tuple 'acc_data_structure'.
Details are in accelerometer_data_structure.py.

Publishes this structure.

Originally written for partial scans from wireless coms which needed assembling.
Assembles fragments of scans and handles multiple scans.

last update: 2025_04_14

@author: matthew oppenheim

'''
import accelerometer_data_structure as ads
import dispatcher_signals as ds
import logging
from pydispatch import dispatcher
import re
import time
import utilities


class Parse_accelerometer_data():
    ''' Parse accelerometer data '''
    # ------- start and end markers of a valid sensor data string
    # used to cobble multiple and split scans together
    ACC_DATA_IDENTIFIER = r' accelerometer.cpp'
    START_MARKER = 'ST'
    END_MARKER = 'EN'

    # regex's to find components of sensor data that need to be parsed out
    # see sensor data example in header
    REGEX_MILLIS = r'(.*\s*m:)(\s*)(?P<millis>.[0-9]+)'
    REGEX_COUNTER = r'(.*\s*c:)(\s*)(?P<counter>.[0-9]+)'
    REGEX_x_acc = r'(.*\s*x:)(\s*)(?P<x_acc>.[0-9]+)'
    REGEX_y_acc = r'(.*\s*y:)(\s*)(?P<y_acc>.[0-9]+)'
    REGEX_z_acc = r'(.*\s*z:)(\s*)(?P<z_acc>.[0-9]+)'

    def __init__(self, delta=100000):
        # delta is the time between scans
        self.time_delta = delta
        # self.partial_scan is used to store incomplete fragments of scans to be added to
        # the start of subsequent scans
        self.partial_scan = None
        self.acc_scan = ads.acc_data_structure
        # ---- identifiers to mark start and end of sensor data reading
        # accelerometer data headers
        self.num_data_fields = len(ads.acc_data_headers) 

    def make_acc_data_structure(data_string):
        ''' Convert a data_string into a acc_data_structure. '''

    def check_counter(self, counter):
        ''' check the counter has incremented correctly '''
        counter_delta = int(counter)-self.old_counter
        # counter_delta will be 2^16 when the counter rolls over
        if counter_delta != 1 or counter_delta !=2^16 :
            logging.error('*** counter delta is {}'.format(counter_delta))


    def check_delta(self, delta):
        ''' check that the time between scans is in spec '''
        if int(delta) > self.time_delta + 100:
            logging.debug('*** delta is {}'.format(delta))


    def check_valid_data(self, data):
        ''' Check if the data is valid sensor data '''
        # crude check that the data is sensor data
        # TO DO: improve this check
        for check_string in [self.ACC_DATA_IDENTIFIER, self.START_MARKER, self.END_MARKER]:
            if check_string in data:
                return True
        return False
        

    def dispatcher_send_data(self, data):
        ''' Publish data '''
        dispatcher.send(signal=ds.PARSER_SIGNAL, sender=ds.PARSER_SENDER, message=data)
        
    
    def extract_single_scan(self, multi_scans, START_MARKER, END_MARKER):
        ''' Return a single scan and the multi_scans-single scan '''
        # index of where the data starts after START_MARKER
        start_index = multi_scans.index(START_MARKER) + len(START_MARKER)
        # index of where the data ends after END_MARKER
        end_index = multi_scans.index(END_MARKER, start_index)
        # single_scan contains a complete scan of sensor data
        single_scan =  multi_scans[start_index:end_index]
        # remove the single_scan from the start of multi_scans
        multi_scans = multi_scans[end_index+len(END_MARKER):]
        return multi_scans, single_scan


    def parse_new_data(self, new_data, START_MARKER=START_MARKER, END_MARKER=END_MARKER):
        ''' Parse all of the received data which may contain multiple scans or fragments. 
        Send complete scans as acc_data_structure's to the dispatcher. '''
        remaining_data = None # to store data after a single_scan is removed from it
        # new_data = new_data.decode()
        if not self.check_valid_data(new_data):
            return None
        # if the previous scan contained the start of a partial scan
        if self.partial_scan:
            # tack the partial start of the scan onto the start of the most recent scan
            new_data=str(self.partial_scan+new_data)
        while True:
            # Repeatedly extract, parse and convert single_scans to acc_data_structure
            # until no data or a partial scan is left.
            try:
                # the returned new_data has single_scan removed from it
                new_data, single_scan = self.extract_single_scan(new_data, self.START_MARKER, self.END_MARKER)
                acc_data_structure = self.parse_single_scan(single_scan)
                # publish the new accelerometer_data_structure using pydispatcher
                self.dispatcher_send_data(acc_data_structure)
            except ValueError:
                # if only a partial scan is left, a ValueError is raised
                # any partial scan left over will be tacked onto the start of the next received scan
                self.partial_scan=remaining_data
                break


# t_watch data parser
    def parse_single_scan(self, single_scan):
        ''' Parse single_scan to an acc_data_structure. '''
        # regex_data needs to match the named groups in a single_scan
        try:
            millis = re.match(self.REGEX_MILLIS, single_scan).group('millis')
        except AttributeError as e:
            logging.error(f'millis regex error: {e}')
            millis = None
        # some type of counter error occurring, perhaps from an overflow, chasing this down
        try:
            counter = re.match(self.REGEX_COUNTER, single_scan).group('counter')
        except AttributeError as e:
            logging.error(f'counter regex error: {e}')
            counter = None
        x_acc = re.match(self.REGEX_x_acc, single_scan).group('x_acc')
        y_acc = re.match(self.REGEX_y_acc, single_scan).group('y_acc')
        z_acc = re.match(self.REGEX_z_acc, single_scan).group('z_acc')
        parsed_string = f'millis: {millis} counter: {counter} x_acc: {x_acc} y_acc: {y_acc} z_acc: {z_acc}'
        # logging.debug(f'parsed_string: {parsed_string}')
        acc_data_structure = ads.acc_data_structure(millis, counter, x_acc, y_acc, z_acc)
        # create an accelerometer data structure
        # publish scan_numpy_row using dispatcher
        return acc_data_structure
    

    

if __name__ == '__main__':
    parse = Parse_accelerometer_data()
