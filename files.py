'''Created on 3 May 2016

@author: matthew oppenheim
Handles creating and writing data to a file.
Written to run in a thread.
Communication to the thread uses a queue.

last update: 2025_04_30
'''
import dispatcher_signals as ds
import datetime
import logging
import os
from pydispatch import dispatcher
import queue # for inter-thread communication
import threading
import time


# as this class does not run in the main thread, __ini__ definition of logging does not work
logging.basicConfig(level=logging.INFO, format='%(message)s')


class Files():

    FILENAME = 'handshake_data.txt' # part of saved data's filename
    
    def __init__(self, queue_in):
        # set up a dispatcher to receive data from the sensor data parser
        dispatcher.connect(self.dispatcher_receive_data,signal=ds.PARSER_SIGNAL, sender=ds.PARSER_SENDER)
        self.overwrite = False
        self.save_data = False
        self.filepath = None # filepath for saved data
        self.queue_in = queue_in # for inter-thread communication from main.py
        self.main()

    
    def main(self):
        while(1):
            # look for a message sent from main.py to the thread this object runs in
            try:
                message = self.queue_in.get()
                self.handle_queue_message(message)
            except AttributeError as e:
                pass
            time.sleep(0.1)


    def create_filepath(self):
        ''' Create a date and time stamped filepath. '''
        datestring = datetime.datetime.now().strftime("%Y_%m_%d:%H:%M:%S")
        filename = f'{datestring}_{self.FILENAME}'
        save_dir = os.path.dirname(__file__) # use this script's directory to save data
        filepath = os.path.join(save_dir, filename)
        logging.info(f'created filepath: {filepath}')
        return filepath


    # must use keyword 'message' in dispatcher setup
    def dispatcher_receive_data(self, message):
        ''' Received data from dispatcher set up in serial_connection.  '''
        if not self.filepath and self.save_data: 
            logging.error('*** no self.filepath')
        # save to file if the filepath exists and self.save_data is True
        if self.filepath and self.save_data:
            self.write_to_file(self.filepath, message)
    

    def handle_queue_message(self, message):
        ''' Handle data received by inter-thread communication queue. '''
        # message shoule only be what the status of self.save_data should be set to
        logging.debug(f'\n*** received queue message {message}\n')
        if message in [True, False]:
            self.save_data = message
        if self.save_data:
            if not(self.filepath):
                self.filepath = self.create_filepath()
                self.initialise_file(self.filepath)
         

    
    def initialise_file(self, file_path):
        ''' Create a blank file. '''
        if os.path.exists(file_path):
            logging.debug('over writing {}'.format(file_path))
        file_object = open(file_path,'wb')
        file_object.close()


    def write_to_file(self, file_path, data):
        ''' Write <data> to <filepath>. '''
        file_object = open(file_path,'a')
        file_object.write(data.__str__())
        file_object.write('\n') # new line


if __name__ == '__main__':
  files = Files()