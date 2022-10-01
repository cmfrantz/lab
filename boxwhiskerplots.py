# -*- coding: utf-8 -*-
"""
Created on Mon July 25 19:08:08 2022

@author: cariefrantz

Imports a CSV with first column the sample names,
additional columns are the different data types,
first row is the name of the different variables.

"""

# IMPORTS
from tkinter import *
from tkinter import filedialog
import pandas as pd
import matplotlib.pyplot as plt
import math


# VARIABLES
title = "Select csv file containing the data"
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
    #data.dropna(how='all', inplace=True)
    return data


def findUniques(alist):
    seen = set()
    seen_add = seen.add
    return [x for x in alist if not (x in seen or seen_add(x))]


      
####################
# MAIN FUNCTION
####################
if __name__ == '__main__': 
    data=importTable(title=title)
    # Separate out the variables
    x_vars=findUniques(list(data.index))
    y_vars=list(list(data.columns))
    
    #Make a seperate plot for each y variable
    fig, axs = plt.subplots(len(y_vars),1, figsize=(8,12))
    for i,var in enumerate(y_vars):
        # Make a 2D array containing the data for each x_variable
        plot_data = {}
        for j,x in enumerate(x_vars):
            plot_data[j]=data[var][x]
            plot_data[j] = [x for x in data[var][x] if math.isnan(x) == False]
        pdata=[list(plot_data[k]) for k in plot_data]
        axs[i].boxplot(pdata, labels=x_vars)
        axs[i].set_ylabel(var)

    