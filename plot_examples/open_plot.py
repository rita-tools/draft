# USAGE:
# add this script as python action in the properties of the vector layer in your QGIS project
# than use identify feature tool and click on the new action under the actions list

import matplotlib
matplotlib.use('qtagg')
import matplotlib.pyplot as plt
import pandas as pd

# file_name is the name of the file that contains the time serie
# the file must be in CSV format and must contain two column: timestamp, rec_value
# timestamp is the time in the form aaaa-mm-day
# rec_value is the values to be plotted as time serie
# columns must be separated by semicolon

# the layer must have a column called FILE with the absolute path to the CSV file
file_name  = r'[%FILE%]'

# open the file with pandas
df = pd.read_csv(file_name, sep=';')
#print(df)
#df.plot( 'timestamp' , 'rec_value' )
plt.plot(df['timestamp'],df['rec_value'])
plt.title('data from '+file_name)
plt.show()