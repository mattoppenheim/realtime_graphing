'''
Created on 3 Apr 2016

@author: matthew
calculations for IMU data, e.g. IMU6050
pitch, roll

https://stackoverflow.com/questions/3755059/3d-accelerometer-calculate-the-orientation
https://engineering.stackexchange.com/questions/3348/calculating-pitch-yaw-and-roll-from-mag-acc-and-gyro-data
Roll = atan2(Y, Z) * 180/PI;
Pitch = atan2(-X, sqrt(Y*Y + Z*Z)) * 180/PI;
to compensate for gimbal lock:
Roll  = atan2( Y,   sign* sqrt(Z*Z+ miu*X*X));
sign  = 1 if accZ>0, -1 otherwise 
miu = 0.001
'''

MIU = 0.001

import logging
import math
import numpy as np

# as this class does not run in the main thread, __ini__ definition of logging does not work
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# length in samples of rolling window used to process dataframe
ROLLING_WINDOW_LENGTH = 8 

class IMU_calcs():
    def __init__(self, rolling_window_length = ROLLING_WINDOW_LENGTH):
        self.rolling_window_length = rolling_window_length
        pass
    
    @staticmethod
    def abs(x, y, z):
        ''' Calculate absolute value of x, y, z. '''
        abs = math.sqrt(x**2+y**2+z**2)
        return abs


    @staticmethod
    def pitch(x, y, z):
        ''' Uses accelerometer values to return pitch. '''
        pitch = np.arctan2(-x, np.sqrt(y**2 + z**2)) *180/np.pi
    #     if z>0:
    #         sign = 1
    #     else:
    #         sign = -1
    #     pitch = np.arctan2(x, sign*np.sqrt(MIU*y**2 + z**2)) *180/np.pi
        return pitch


    @staticmethod
    def roll(x, y, z):
        ''' Uses accelerometer values to return roll. '''
        if z>0:
            sign = -1
        else:
            sign = 1
        roll = np.arctan2(y,sign*np.sqrt(z**2+MIU*x**2))*180/np.pi
        return roll


    @staticmethod
    def yaw(x, y, z):
        ''' Uses accelerometer values to return yaw. '''
        # yaw = 180 * atan (accelerationZ/sqrt(accelerationX*accelerationX + accelerationZ*accelerationZ))/M_PI;
        yaw = 180 * np.arctan(z/np.sqrt(x**2 + z**2))/np.pi;
        return yaw 


    def update_df(self, df):
        # update df containing x,y,z accelerometer data with pitch, roll, yaw, absolute acceleration
        # extract x,y,z from dataframe
        x = df['acc_x'].tolist()[0]
        y = df['acc_y'].tolist()[0]
        z = df['acc_z'].tolist()[0]
        # pitch = self.pitch(x, y, z)
        # roll = self.roll(x, y, z)
        # yaw = self.yaw(x, y, z)
        acc_abs = self.abs(x, y, z)
        # update first row of pitch, roll, yaw, acc_abs dataframe columns
        # df.loc[0,'pitch'] = pitch
        # df.loc[0,'roll'] = roll
        # df.loc[0,'yaw'] = yaw
        df.loc[0,'acc_abs'] = acc_abs
        logging.debug(f'acc_y:{y:.2f} abs:{acc_abs:.2f}')
        return df


