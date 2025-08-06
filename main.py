'''
graph x,y,z accelerometer data coming from T-Watch S3
See README.md for full details of program architecture.
Part of the handshake project: mattoppenheim.com/handshake
The graphing thread has to run as the main thread - don't try to move
this into another class and instantiate it from main.
Connect with the T-Watch using a USB cable.
The connection creates a serial port: /dev/ACM* (linux) or /dev/ttyUSB* (windows)
Dependencies:
  PyDispatcher, pyserial, pyqtgraph, numpy, scikit, PySide6, pyopengl, pyzmq
@author: matthew oppenheim
last date of update: 2025_04_29

TO DO: Add data save and replay
'''

#import accelerometer_data_structure as ads
# import imu_calcs
import accelerometer_data_structure as ads
from dataframe import DataFrame
import dispatcher_signals as ds
from files import Files # save data to file
from imu_calcs import IMU_calcs
import logging
import math # math.sqrt math.isnan used
import numpy as np # np.clip used
import pandas as pd
import PySide6
from pydispatch import dispatcher
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import queue # for inter-thread communiction
from replay_data import ReplayData
# from gesture import Gesture
from serial_connection import Serial_Connect
# from shake_recognition import Shake_Recognition
import sys
import threading
import time
import utilities

# display will have limits +/- AMPLITUDE
# AMPLITUDE = 2

UPDATE_MS = 100 # how fast to update graph in ms

class Handshake():

    LOG_UPDATE_INTERVAL = 1 # time in s inbetween writing data to textedit box
    MAX_ACC = 512 # max value to plot for accelerometer axis
    MIN_ABS = 400 # min value for absolute acceleration
    MAX_ABS = 750 # min value for absolute acceleration
    MAX_ROLL = 180 # roll varies from +180 to -180
    MAX_PITCH = 90 # pitch varies from +90 to -90
    MAX_YAW = 90 # yaw varies from +180 to -180
    SENSOR_TIME_SAMPLES = 200 # how many samples to average over to find sensor update frequence
    WIN_X = 300 # graph size in x
    WIN_Y = 500 # graph size in y

    def __init__(self):

        # set up a dispatcher to receive data from the sensor data parser
        dispatcher.connect(self.dispatcher_receive_data,signal=ds.PARSER_SIGNAL, sender=ds.PARSER_SENDER)

        # ---- setup dataframe that stores sensor and filtered data
        self.dataframe = DataFrame()
        self.df = None # dataframe with data to plot is retrieved using dataframe_handler
        # ----- Set up the serial connection and run in a thread
        # create the serial port connection, do not instantiate this from the main class
        # or it blocks the program
        serial_connection_thread = threading.Thread(target=Serial_Connect)
        serial_connection_thread.start()
        self.last_graph_update = time.time() # used to measure the graph update frequency, independent of sensor data frequency
        self.last_textedit_update = time.time() # used to limit update rate of textedit box
        self.queue_out = queue.Queue(maxsize=1) # for inter-thread communication
        self.file_thread = threading.Thread(target=Files, args=(self.queue_out,)) # starts in a thread
        self.file_thread.start() # start the thread
        self.time_list = [0] * self.SENSOR_TIME_SAMPLES # empty list of time stamps to calculate graph update rate
        self.imu = IMU_calcs()
        self.play = True # should the graph scroll, for play/pause button
        self.record = False # should the data be saved to file
        # ----- Set up the graphs
        self.create_graphs()
        self.create_buttons()
        self.create_textbox()
        logging.debug('\n*** display setup\n')


    def create_graphs(self):
        ''' Create the graphs. '''
        pg.setConfigOption('background', 'w')
        acc_pen = pg.mkPen(color='blue', width=3)
        focus_pen = pg.mkPen(color='orange', width=3)
        pen = pg.mkPen(color='black', width=3)
        self.win = pg.GraphicsLayoutWidget(show=True, title='T-Watch accelerometer data')
        self.win.setWindowTitle('T-Watch accelerometer data')
        self.win.resize(self.WIN_X,self.WIN_Y)
        pg.setConfigOptions(antialias=True)
        self.p_xacc = self.win.addPlot(title='acc_x')
        self.win.nextRow()
        self.p_yacc = self.win.addPlot(title='acc_y')
        self.win.nextRow()
        self.p_zacc = self.win.addPlot(title='acc_z')
        self.win.nextRow()
        ''' pitch, roll, yaw not in use
        self.p_pitch = self.win.addPlot(title='pitch')
        self.win.nextRow()
        self.p_roll = self.win.addPlot(title='roll')
        self.win.nextRow()
        self.p_yaw = self.win.addPlot(title='yaw')
        self.win.nextRow()
        '''
        # data created by processing accelerometer data
        self.p_abs = self.win.addPlot(title='abs') # absolute value of all 3 axis
        self.win.nextRow()
        # how much current value exceeds mean in a window preceding the current value
        self.p_y_exceeded_mean = self.win.addPlot(title='y_exceeded_mean_abs')
        # accelerometer axis graphs
        self.p_xacc.setYRange(-self.MAX_ACC,self.MAX_ACC)
        self.p_yacc.setYRange(-self.MAX_ACC,self.MAX_ACC)
        self.p_zacc.setYRange(-self.MAX_ACC,self.MAX_ACC)
        ''' pitch, roll, yaw not in use
        # pitch, roll, yaw calculated in imu_calcs.py
        self.p_pitch.setYRange(-self.MAX_PITCH,self.MAX_PITCH)
        self.p_roll.setYRange(-self.MAX_ROLL,self.MAX_ROLL)
        self.p_yaw.setYRange(-self.MAX_YAW,self.MAX_YAW)
        '''
        self.p_abs.setYRange(self.MIN_ABS,self.MAX_ABS)
        self.p_y_exceeded_mean.setYRange(0,self.MAX_ABS)
        # assign graph line names
        self.curve_xacc = self.p_xacc.plot(pen=acc_pen)
        self.curve_yacc = self.p_yacc.plot(pen=acc_pen)
        self.curve_zacc = self.p_zacc.plot(pen=acc_pen)
        ''' pitch, roll, yaw not in use
        self.curve_pitch = self.p_pitch.plot(pen=pen)
        self.curve_roll = self.p_roll.plot(pen=pen)
        self.curve_yaw = self.p_yaw.plot(pen=pen)
        '''
        self.curve_abs = self.p_abs.plot(pen=pen)
        self.curve_y_exceeded_mean = self.p_y_exceeded_mean.plot(pen=focus_pen)


    def create_buttons(self):
        ''' Add control buttons to self.win. '''
        # create play/pause button to play or pause the sensor data display
        # data continues being read, only the display is frozen
        pause_button_proxy = QtWidgets.QGraphicsProxyWidget()
        self.pause_button = QtWidgets.QPushButton('play/pause')
        self.pause_button.clicked.connect(self.pause_button_clicked)
        pause_button_proxy.setWidget(self.pause_button)
        self.pause_button_update_appearance()
        self.win.nextRow()
        self.win.addItem(pause_button_proxy)
        # create save button to save data to file
        save_button_proxy = QtWidgets.QGraphicsProxyWidget()
        self.save_button = QtWidgets.QPushButton('save/don\'t save')
        self.save_button.clicked.connect(self.save_button_clicked)
        save_button_proxy.setWidget(self.save_button)
        self.save_button_update_appearance()
        self.win.nextRow()
        self.win.addItem(save_button_proxy)


    def create_textbox(self):
        ''' Add a textbox to self.win. '''
        # text box
        self.win.nextRow()
        self.textedit = QtWidgets.QTextEdit()
        self.textedit.setReadOnly(True)
        textedit_proxy = QtWidgets.QGraphicsProxyWidget()
        textedit_proxy.setWidget(self.textedit)
        self.win.addItem(textedit_proxy)


    # must use keyword 'message' in dispatcher setup
    def dispatcher_receive_data(self, message):
        ''' Received data from dispatcher set up in serial_connection.  '''
        # message is a acc_data structured tuple with data for a single accelerometer x,y,z scan
        self.df = self.dataframe.update_dataframe(message)
        # update sensor columns to self.df
        self.df = self.imu.update_df(self.df)
        # for debugging:
        self.log_df()


    def display_update_rates(self):
        ''' Print graph and sensor update rates to self.log_textedit. '''
        now_time = time.time()
        # write periodically or the display is swamped
        if (now_time - self.last_textedit_update) > self.LOG_UPDATE_INTERVAL:
            # write graph update rate to self.textedit
            graph_update_frequency = self.graph_update_rate()
            sensor_update_frequency = self.sensor_update_rate()
            try:
                self.log_textedit(f'graph fy: {graph_update_frequency:5.2f} sensor fy:{sensor_update_frequency:5.2f}')
            except TypeError as e: # no sensor data causes a typerror
                pass
            self.last_textedit_update = now_time


    def graph_update_rate(self):
        ''' Calculate graph refresh frequency. '''
        # This is independent of the sensor data.
        update_frequency = None
        self.time_list = self.time_list[1:]
        cleaned_time_list = [x for x in self.time_list if x != 0 ] # remove 0s from time_list
        if len(cleaned_time_list)>1:
            try:
                update_frequency = (len(cleaned_time_list)-1)/(cleaned_time_list[-1] - cleaned_time_list[0])
            except ZeroDivisionError as e:
                return None
        return update_frequency


    def log_df(self):
        ''' Log df values for row 0 '''
        acc_x = self.df.loc[0,'acc_x']
        acc_y = self.df.loc[0,'acc_y']
        acc_z = self.df.loc[0,'acc_z']
        ''' pitch, roll, yaw not in use
        pitch = self.df.loc[0,'pitch']
        roll = self.df.loc[0,'roll']
        yaw = self.df.loc[0,'yaw']
        '''
        acc_abs = self.df.loc[0,'acc_abs']
        millis = self.df.loc[0,'millis']
        counter = self.df.loc[0,'counter']
        y_exceeded_mean = self.df.loc[17, 'y_exceeded_mean']
        #logging.debug(f'acc_x:{acc_x:7.2f} acc_y:{acc_y:7.2f} acc_z:{acc_z:7.2f} pitch:{pitch:7.2f} roll:{roll:7.2f} yaw:{yaw:7.2f} abs:{acc_abs:7.2f}, millis:{millis:12.0f}, counter:{counter:8.0f}')
        # logging.debug(f'acc_x:{acc_x:7.2f} acc_y:{acc_y:7.2f} acc_z:{acc_z:7.2f} abs:{acc_abs:7.2f}, millis:{millis:12.0f}, counter:{counter:8.0f}')
        logging.debug(f'acc_x:{acc_x:7.2f} acc_y:{acc_y:7.2f} acc_z:{acc_z:7.2f} abs:{acc_abs:7.2f}, y_exceeded_main:{y_exceeded_mean:7.2f}')


    def log_textedit(self, text):
        ''' Write text to self.textedit. '''
        text = ('{} {}\n'.format(utilities.now_time_simple(), text))
        self.textedit.moveCursor(QtGui.QTextCursor.End)
        self.textedit.insertPlainText(text)


    def pause_button_clicked(self):
        ''' Toggle play/pause button and self.play. '''
        self.play = not(self.play)
        self.pause_button_update_appearance()
        logging.debug(f'play-pause button: {self.play}')


    def pause_button_update_appearance(self):
        ''' Set the pause button appearance. '''
        if not self.play:
            self.pause_button.setText('paused')
            self.pause_button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: red;}')
        else:
            self.pause_button.setText('playing')
            self.pause_button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: green;}')


    def save_button_clicked(self):
        ''' Toogle save button and self.save. '''
        self.record = not(self.record) # toggle recording on or off
        self.queue_out.put(self.record) # send self.record to thread running file handler
        self.save_button_update_appearance()
        logging.debug(f'record button: {self.record}')
        self.log_textedit(f'recording to file: {self.record}')


    def save_button_update_appearance(self):
        ''' Set the save button appearance. '''
        if not self.record:
            self.save_button.setText('not saving data')
            self.save_button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: green;}')
        else:
            self.save_button.setText('recording data to file')
            self.save_button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: blue;}')


    def sensor_update_rate(self):
        ''' Calculate the sensor update frequency. '''
        # find first and last none NaN indices
        update_frequency = 0
        try:
            millis_list = self.df['millis'].tolist()
        except TypeError as e:  # no data causes a Typerror
            return
        cleaned_millis_list = [x for x in millis_list if not math.isnan(x)]
        if len(cleaned_millis_list)>1:
            try:
                update_frequency = 1000*(len(cleaned_millis_list)-1)/(cleaned_millis_list[0] - cleaned_millis_list[-1])
            except ZeroDivisionError as e:
                return None
        return update_frequency


    def timer_timout(self):
        ''' Triggered by QTimer timeout. '''
        self.update_line_graphs()
        # append now_time to self.time_list to calculate update rate
        now_time = time.time()
        # append new time to time_list then roll the list down
        self.time_list.append(now_time)
        self.display_update_rates() # display graph and sensor update rates


    def update_line_graphs(self):
        ''' Update all of the accelerometer and other line graphs. '''
        # check that the play/pause button is set to play
        if not self.play:
            return
        try:
            acc_x = self.df['acc_x'].to_numpy()
            acc_y = self.df['acc_y'].to_numpy()
            acc_z = self.df['acc_z'].to_numpy()
            ''' pitch, roll, yaw not in use
            pitch = self.df['pitch'].to_numpy()
            roll = self.df['roll'].to_numpy()
            yaw = self.df['yaw'].to_numpy()
            '''
            abs = self.df['acc_abs'].to_numpy()
            y_exceeded_mean = self.df['y_exceeded_mean'].to_numpy()
            self.curve_xacc.setData(acc_x)
            self.curve_yacc.setData(acc_y)
            self.curve_zacc.setData(acc_z)
            ''' pitch, roll, yaw not in use
            self.curve_pitch.setData(pitch)
            self.curve_yaw.setData(yaw)
            self.curve_roll.setData(roll)
            '''
            self.curve_abs.setData(abs)
            self.curve_y_exceeded_mean.setData(y_exceeded_mean)
        except TypeError as e:
            logging.debug('no data to update')



# **** not in use
    def write_array_file(self, new_np_array, old_np_array):
        ''' write sensor numpy array to file '''
        # need to add new data onto end of old array
        self.save_data.write_numpy_array_to_file(new_np_array, old_np_array)


if __name__ == '__main__' :
    handshake = Handshake()

    timer = pg.QtCore.QTimer()
    timer.timeout.connect(handshake.timer_timout)

    # timer units are milliseconds. timer.start(0) to go as fast as practical.
    timer.start(UPDATE_MS) # timer timeout in ms
    pg.exec()
