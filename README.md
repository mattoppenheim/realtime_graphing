# Notes

To automagically run each time that main.py is saved:
while inotifywait -e close_write main.py ; do make run ; done

# handshake project accelerometer data plotting

Matthew Oppenheim 2025

main.py is the entry point

Display x,y,z accelerometer data from Lilygo T-Watch S3.
Display filtered data created using the accelerometer data.
Part of the handshake project.
The T-Watch connects via a serial port, /dev/ttyACM0 on Linux.
main.py instantiates a Handshake object.
The Handshake object instantiates a Serial_Connect object in a thread.
The T-Watch accelerometer data is collected by a Serial_Connect object.
Any data that is read by by the Serial_Connect object is parsed using a Parse_accelerometer_data object.
The parsed data is made available as an accelerometer_data_structure (ads) named tuple using pydispatcher.
The dispatcher is in parse_accelerometer.dispatcher_send_data.
Handshake subscribes to this dispatcher and sends the ads to a Dataframe object.
In the Dataframe object, the parsed data is added to a pandas dataframe.
I've read that this is computationally inefficient compared with creating e.g. lists and then creating a pandas dataframe from the list.
However, it works and I understand it which are two good reasons for running as is.
main.py collects the updated dataframe and plots columns from this.

## To do

Filtering and additional data sets can be created using the pandas dataframe.
Stop/start button.
Save data. 
Enable the program to run using saved data as the source instead of using data from a serial port.


# serial_connection

finds and creates a serial port connection with the t_watch
Instantiates a Parse_acceleromter_data object.
Periodically looks for new data on the serial port.
Sends data read from the serial port to the parse_accelerometer_data object.

# parse_accelerometer_data

Checks that the received data is sensor data.
Splits the received sensor data into complete sensor data scans.
Parses a single scan into a accelerometer_data_structure (ads) named tuple. 
Pulishes this ads using dispatcher pub/sub.
Repeatedly reads complete scans from the received data until there is no data or an incomplete scan left.
If an incomplete scan is left, this is added to the start of the next data packet received for parsing.

# main.py

pyqtgraph is used for graphing.
Creates the GUI. Don't try and put the graphing into a separate class. The thread that runs the graphs needs to be the main thread.
I've wasted some hours of my life repeatedly proving this.
Sets up a dispatcher to receive data from the parse_accelerometer_data object that will be instantiated in serial_connection.
Instantiates Serial_Connect in a thread.

# dataframe.py

Creates an empty pandas dataframe.
Updates the pandas dataframe with new data, removing oldest data.
New data is entered as row 0 after shifting all of the dataframe rows up by 1.
I've read that it is more efficient to create e.g. lists of data then create pandas dataframes directly rather than add to a dataframe.
Did some optimisation so that the dataframe size is constant. See timings section for test results.
A fixed size dataframe is created. Existing data is moved up one row using shift, then new data is written as row 0.
Returns the updated pandas dataframe when requested.
The dataframe contains the data that is plotted in the Handshake object.

# imu_calcs.py

Calculates pitch, roll, yaw and absolute acceleration.
Adds these values to row 0 of a supplied dataframe in the appropriate columns.

# timings

Tested using a jupyter notebook. Created a pandas dataframe 300 rows long, 5 columns wide.
Added a row and removed a row 1000 times. Total for 1000 iterations is 0.3245s.
Instead of adding and removing a row, shift the dataframe -1 rows. Replace last row with the latest scan. 3x faster than removing and concatenating dataframes.
Created a numpy array, same size, same operation. Total for 1000 iterations is 0.0092s.
Problem: numpy array cannot have named columns? Could use a structured array with the ads as the elements?

# tests

Run from scripts directory (not tests directory) using:
```
python -m pytest
```

