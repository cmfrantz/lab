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
import numpy as np
import matplotlib.pyplot as plt
import math
import re


# VARIABLES
title = "Select xls file containing the data"
# Define data row and columns
head_row = 0
head_col = 0
ftypes = {
    'Excel' : ['xls', 'xlsx'],        
    'CSV'   : ['csv']
    }
mass_col = 'Mass sample (g)'
blank_rows = [0,1,2,3]

# EPA Soil Screening Levels for ingestion (mg/kg = ppm)
# From https://semspub.epa.gov/work/HQ/175213.pdf
epa_ssl = {
    'Sb' : 31,
    'As' : 0.4,
    'Ba' : 5500,
    'Be' : 0.1,
    'Cd' : 78,
    'Cr' : 390,
    'Pb' : 400,
    'Ni' : 1600,
    'Se' : 390,
    'Ag' : 390,
    'V'  : 550,
    'Zn' : 23000
    }


# FUNCTIONS

def importTable (title, head_row=0, head_col=0, data_start_row=1,
                 data_start_col=1, ftypes={'CSV' : ['csv']}):
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
    data_start_row : int, optional
        Row number containing the first row of data to read in.
        The default is 1 (second row)
    data_start_col : int, optional
        Column number containing the first column of data to read in.
        The default is 1 (second column)
    ftypes  : dict, optional
        Dictionary containing filetypes matched to lists of file extensions.
        The default is CSV files only:  {'CSV' : ['csv']}

    Returns
    -------
    filepath : string
        Path of the file opened.
    data : pandas DataFrame
        DataFrame containing the measured values for each x,y location for
        any number of different measurements (as columns).

    '''
    # Generate filetype list
    filetypes=[]
    for ftype in ftypes:
        fexts = ''
        for i, fext in enumerate(ftypes[ftype]):
            if i==len(ftypes[ftype])-1:
                fexts = fexts + '*.' + fext
            else:
                fexts = fexts + '*.' + fext + ', '
        filetypes.append((ftype, fexts))
        
    
    # Select the spreadsheet
    root = Tk()
    filepath = filedialog.askopenfilename(title = title, filetypes = filetypes)
    root.destroy()
    
    # Determine filetype
    file_ext = filepath.split(".")[1]
    
    # Read in the spreadsheet
    if file_ext in ['xls','xlsx']:
        data = pd.read_excel(
            filepath, header = head_row, index_col = head_col)
    elif file_ext == 'csv':
        data = pd.read_csv(
            filepath, sep=',', header = head_row, index_col = head_col)
    
    # Delete extra rows and columns
    #delrows = data_start_row - head_row -1
    #delcols = data_start_col - head_col -1
    data.dropna(how='all', inplace=True)
    return filepath, data


def findUniques(alist):
    seen = set()
    seen_add = seen.add
    return [x for x in alist if not (x in seen or seen_add(x))]

#%%
      
####################
# MAIN FUNCTION
####################
if __name__ == '__main__': 
    fpath, data = importTable(title=title, ftypes=ftypes)
    isotopes = list(data.columns)[1:]
    
    # Normalize to sample mass & put in units of ng/g (ppb)
    data_norm = data[isotopes].divide(data[mass_col], axis='index')*100
    
    # Delete negative values
    # data_noneg = data.copy()
    # data_noneg[data_noneg < 0] = 0
    
    # Determine the size of the plot grid
    n_plot_cols = 6
    n_plot_rows = math.ceil(len(isotopes)/n_plot_cols)
    
    #%%
    #fig, axs = plt.subplots(n_plot_rows, n_plot_cols)
    fig, axs = plt.subplots(
        n_plot_rows, n_plot_cols, figsize=(len(isotopes)*2+1,n_plot_rows*7))

    # Build the plots
    for i, isotope in enumerate(isotopes):
        
        # Track the plot number (for debugging)
        print("plot " + str(i) + ": " + isotope)
        
        # Determine where to put the plot
        plot_row = math.ceil((i+1)/n_plot_cols)-1
        plot_col = i-n_plot_cols*plot_row
        
        # Plot the data
        axs[plot_row,plot_col].bar(
            list(data_norm.index), data_norm[isotope], edgecolor="white")
                
        # Plot max in the blanks
        blank_max = max(data_norm.iloc[blank_rows][isotope])
        axs[plot_row,plot_col].axhline(y=blank_max)
        
        # Determine EPA limit
        # Identify the element
        element = re.findall(r'(\d+)(\w+?)', isotope)[0][1]
        a = list(data_norm[isotope])
        # If element has an EPA limit, add it to the plot
        if element in list(epa_ssl):
            ssl = epa_ssl[element]*1E3
            a.append(ssl)
            axs[plot_row,plot_col].axhline(y=ssl,color='r')
        
        # Set the y limits & label y
        axs[plot_row,plot_col].set_ylim([0,math.ceil(max(a)*1.02)])
        axs[plot_row,plot_col].set_ylabel(isotope + " (ppb)")

        # Label x axis & add title                
        axs[plot_row,plot_col].set_xticklabels(
            list(data_norm.index), rotation = 90)
        axs[plot_row,plot_col].set_title(isotope)
        

        
        
        

                               
                     