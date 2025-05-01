''' Create and update a data array.
Part of the handshake project: mattoppenheim.com/handshake
Sensor data is stored in a pandas dataframe.
New scans are added to the end of the dataframe.
Old scans are removed from the start of the array.
Sensor data in stored in columns 0-x.
Extra columns of processed data are added beyond row x
The pandas dataframe is used by a graph display class to create plots.

Author: Matthew Oppenheim
Last update: 2025_04_14
'''
import accelerometer_data_structure as ads
import logging
import numpy as np # using np.nan to initialise dataframe
import pandas as pd

# as this class does not run in the main thread, __ini__ definition of logging does not work
logging.basicConfig(level=logging.INFO, format='%(message)s')

class DataFrame():

  # MAX_DATAFRAME_ROWS = 300 # data_array size
  # *** FOR TESTING
  MAX_DATAFRAME_ROWS = 200 # data_array size
  PROCESSING_HEADERS = ['abs_acc', 'pitch', 'roll', 'yaw']

  def __init__(self):
    # create an empty array for storing data
    self.df_col_names = ads.acc_data_headers + self.PROCESSING_HEADERS
    # initialise a dataframe filled with 0's so that graphs of column data start full-size
    self.df = self.initialise_df(self.df_col_names, self.MAX_DATAFRAME_ROWS)
    logging.debug(f'self.df:\n{self.df}')


  def create_acc_scan_df(self, acc_data):
    ''' Create a pandas dataframe row representing accelerometer sensor data. '''
    # acc_data_structure is a named tuple described in accelerometer_data_structure.py
    millis = acc_data.millis
    counter = acc_data.counter
    x_acc = acc_data.x_acc
    y_acc = acc_data.y_acc
    z_acc = acc_data.z_acc
    scan_data = [millis, counter, x_acc, y_acc, z_acc] # ads.acc_data_structure
    df_single_scan = pd.DataFrame([scan_data], columns=ads.acc_data_headers, dtype=float)
    # need to add extra columns and intialise to 0
    df_single_scan[self.PROCESSING_HEADERS] = 0
    return df_single_scan
  
  
  def initialise_df(self, col_names, num_rows):
    ''' Create a pandas dataframe to store ads data. '''
    row_range = range(num_rows)
    # create a dataframe with 0's, number rows = num_rows
    df = pd.DataFrame(np.nan, index=row_range, columns=col_names)              
    return df


# I've read that this is inefficient timewise - see README.md for timings
  def update_dataframe(self, acc_scan_to_add):
    ''' Shift all rows in self.df down one row and insert df_to_add as last row.  '''
    # convert acc_scan_to_add to a dataframe
    df_to_add = self.create_acc_scan_df(acc_scan_to_add)
    # have to convert df_to_add to a list of lists then extract first element
    df_to_add_as_list = df_to_add.values.tolist()[0] 
    # shift all the rows in the dataframe up 1 - oldest row is removed this way
    self.df = self.df.shift(1)
    # first row is now all NaN's. Replace this with df_to_add_as_list
    self.df.loc[0,:] = df_to_add_as_list # row 0, all columns = df_to_add_as_list
    #logging.debug(f'\nself.df.head():\n{self.df.head()}')
    return self.df
    

if __name__ == '__main__':
   data_array = DataFrame()