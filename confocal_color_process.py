# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 13:24:47 2022

@author: cariefrantz

Script compiles multicolor channel measurements from imagej (saved as csv file)

"""


# IMPORTS
from tkinter import *
from tkinter import filedialog
import pandas as pd
import numpy as np

# VARIABLES
title = "Select csv file containing the color analysis data"
# Define data row and columns
head_row = 0
head_col = 1
channels = {
    'C1'    : 'DAPI',
    'C2'    : 'Calcein',
    'C3'    : 'Chlorophyll'
    }


# FUNCTIONS

def importData(title, head_row=0, head_col=0):
    '''
    Imports table from csv

    Parameters
    ----------
    title : str
        Title for the file selection dialog.
    head_row : int, optional
        Row number containing the column headers.
        Data should immediately follow.
        The default is 0 (first row)
    head_col : int, optional
        Column number containing the sample/data names or index.
        Data should immediately follow.
        The default is 0 (first column)

    Returns
    -------
    data : pandas DataFrame
        DataFrame containing the table.

    '''
    # Import spreadsheet
    root = Tk()
    filepath = filedialog.askopenfilename(title = title,
                                      filetypes = [('CSV', '*.csv')])
    root.destroy()
    data = pd.read_csv(filepath, sep = ',', header = head_row,
                       index_col = head_col)
    data.dropna(how='all', inplace=True)
    return filepath, data

#%%
      
####################
# MAIN FUNCTION
####################
if __name__ == '__main__': 
    filepath,data=importData(title=title, head_row=head_row, head_col=head_col)
    meas_list=list(data.columns)
    meas_list.remove(' ')
    data=data[meas_list]
    
    # Separate out the channels from the name of the file
    fname_split = pd.DataFrame(
        [fname.split('-',1) for fname in list(data.index)])
    data['channel']=list(fname_split.iloc[:,0])
    data['image_file']=list(fname_split.iloc[:,1])

    # Find the unique files
    file_list = list(set(data['image_file']))
    
    # Create a new dataframe that groups the results by file and channel
    channel_list = list(channels)
    header = pd.MultiIndex.from_product([channel_list,
                                     meas_list],
                                    names=['channel','meas'])
    grouped_data = pd.DataFrame(index=file_list, columns=header)
    for file in file_list:
        print(file)
        for channel in channel_list:
            data_index = channel + '-' + file
            channel_data = data.loc[data_index,meas_list]
            for meas in meas_list:
                grouped_data.loc[file,(channel,meas)]=channel_data[meas]
                
    # Save the grouped dataframe
    fpath = filepath.split('.',1)[0]
    grouped_data.to_csv(fpath+'_grouped.csv')        
    