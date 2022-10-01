# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 12:08:08 2022

@author: cariefrantz
"""

# IMPORTS
from tkinter import *
from tkinter import filedialog
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# VARIABLES
# Define data row and columns
head_row = 0
head_col = 0
x_head = 'x'
y_head = 'y'


# FUNCTIONS

def importTable (title, head_row=0, head_col=0, x_head='x', y_head='y'):
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
    x_head : str, optional
        Column header for the x location data. The default is 'x'.
    y_head : str, optional
        Column header for the y location data. The default is 'y'.

    Returns
    -------
    data : pandas DataFrame
        DataFrame containing the measured values for each x,y location for
        any number of different measurements (as columns).

    '''
    # Import spreadsheet
    root = Tk()
    file = filedialog.askopenfilename(title = title,
                                      filetypes = [('CSV', '*.csv')])
    root.destroy()
    data = pd.read_csv(file, sep = ',', header = head_row,
                       index_col = head_col)
    data.dropna(how='all', inplace=True)
    return data


def metalResults():
    '''Makes 9x3 grid of 3x3 heatmaps of normalized metal concentrations'''
    data = importTable('Select ICP-MS results CSV')
    # Produce plot grid & individual plots
    metal_list = list(data.columns)[3:]
    rows = 3
    cols = 9
    vals = rows*cols
    fig, axs = plt.subplots(rows, cols, figsize=(30,10))    
    fig.suptitle('Normalized metal concentrations in stream grid', fontsize=16)
    
    # Loop through metals and plot   
    for val in list(range(vals)):
        # Set up subplot
        if val == 0:
            cbar = True
            xticklabels=('L','M','R')
            yticklabels=('Up','Mid','Down')
        else:
            cbar = False      
            xticklabels=False
            yticklabels=False
        ax = plt.subplot(rows,cols,val+1)
        # Build plot       
        metal = metal_list[val]
        data_formatted = data.pivot(index='y',columns='x', values=metal)
        max_val = max(data_formatted.max())
        data_norm = data_formatted/max_val
        sns.heatmap(data_norm, ax=ax, square=True, xticklabels=xticklabels,
                    yticklabels=yticklabels, cbar=cbar, vmin=0, vmax=1,
                    cmap=sns.color_palette("Greys", as_cmap=True))
        ax.set_title(metal)
        ax.set(xlabel=None, ylabel=None)
    
