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
title = '''Select csv file containing the grouped color analysis
(output of confocal_color_process) with metadata added'''
# Define data row and columns
head_row = [0,1]
head_col = 0
channels = {
    'C1'    : 'DAPI',
    'C2'    : 'Calcein',
    'C3'    : 'Chlorophyll'
    }
meas_list = ["Mean"]


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
    # Import the file table
    filepath,data=importData(title=title, head_row=head_row, head_col=head_col)
    
    # Create sample IDs
    data[("metadata","sample_id")] = (
        data[("metadata","sample_date")].astype(str) +"_"
        + data[("metadata","sample")].astype(str) + "_"
        + data[("metadata","objective")].astype(str)
        )
    
    # Find the unique sample ids
    unique_ids = list(set(data[("metadata","sample_id")]))
    
    # Create a new dataframe for the summary statistics
    stats=["N","avg","stdev"]
            
    headers = pd.MultiIndex.from_product([channels, meas_list, stats],
                                    names=['channel','meas','stat'])
            
    summary = pd.DataFrame(index=unique_ids, columns=headers)
    
    # Calculate summary statistics for each unique ID
    for sample in unique_ids:
        sample_set = data[data[("metadata","sample_id")]==sample]
        for channel in channels:
            for meas in meas_list:
                summary.loc[sample,(channel,meas,"N")] = len(sample_set)
                summary.loc[sample,(channel,meas,"avg")] = np.mean(sample_set[(channel,meas)])
                summary.loc[sample,(channel,meas,"stdev")] = np.std(sample_set[channel,meas])
                
    # Save the summary statistics
    fpath = filepath.split('.',1)[0]
    summary.to_csv(fpath+'_summary.csv')
        
        
        
    '''
    
    # Create a new dataframe that groups the results by file and channel
    channel_list = list(channels)
    header = pd.MultiIndex.from_product([channel_list,
                                     meas_list],
                                    names=['channel','meas'])
    grouped_data = pd.DataFrame(index=file_list, columns=header)
    for file in file_list:
        for channel in channel_list:
            data_index = channel + '-' + file
            channel_data = data.loc[data_index,meas_list]
            for meas in meas_list:
                grouped_data.loc[file,(channel,meas)]=channel_data[meas]
                
    # Save the grouped dataframe
    fpath = filepath.split('.',1)[0]
    grouped_data.to_csv(fpath+'_grouped.csv')        
    '''
    