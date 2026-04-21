# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 11:56:05 2026

@author: cariefrantz

How hard is it to get rid of invasive plants?
Estimates the number of weed plants present after an uprooting and deadheading
campaign under different scenarios.

"""
# IMPORTS
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# VARIABLES
years = 10              # years to run
colormap = 'viridis'      # colormap to use in plots

# Assumptions
plants_start = 1        # starting plants per m^3
seeds_start = 10        # starting seeds per m^3
plant_max = 50          # maximum number of pmants per m^3
seed_delivery = 0.5     # annual seeds delivered per m^3 from external sources
seed_production = 400   # number of seeds per plant
seed_germination = 0.3  # fraction of dispersed seeds that germinate

# Scenarios
uproot_scenarios = [0,25,50,75,95,100]    # percent of plants to uproot, list of scenarios to run
deadhead_scenarios = [50,75,90,95,100]    # percent of remaining plants to deadhead, list of scenarios to run


# FUNCTIONS

# Annual loop
def runSeason(plant_start, seed_start, percent_uproot, percent_deadhead):
    # Spring: seeds germinate and plants grow
    n_plants_spr = (seed_start + seed_delivery) * seed_germination
    if n_plants_spr > plant_max: n_plants_spr = plant_max
    
    # Picking & deadheading
    n_plants = n_plants_spr * (1-percent_uproot/100)
    n_seedplants = n_plants * (1-percent_deadhead/100)
    
    # Plants produce seeds
    n_seeds = n_seedplants * seed_production
    
    return n_plants_spr, n_plants, n_seeds

#%%

# MAIN

# Set up plots
#fig, axs = plt.subplots(len(uproot_scenarios))   # One plot per uproot scenario
cmap = plt.get_cmap(colormap+'_r')
colors=cmap(np.linspace(0, 1, len(deadhead_scenarios)))

# Run through each uproot scenario (unique plots)
for i, percent_uproot in enumerate(uproot_scenarios):
    
    # Set up the blank table
    result_table = pd.DataFrame(index=list(range(years)))
    
    # Run through each deadhead scenario (unique lines)
    for j, percent_deadhead in enumerate(deadhead_scenarios):
        coltitle = str(percent_deadhead) + '% deadheaded'
        plants = plants_start
        seeds = seeds_start
        # Run through each year
        for x in range(years+1):
            # Calculate number of plants and seeds
            plants_spr, plants, seeds = runSeason(plants, seeds, percent_uproot, percent_deadhead)
            result_table.loc[x,coltitle]=plants_spr
        # Add line to plot
        plt.plot(result_table.index, result_table[coltitle], color=colors[j], label=coltitle)
    
    # Add plot title and legend
    plt.title('Scenario: ' + str(percent_uproot) + '% uprooted')
    plt.xlabel('year')
    plt.ylabel('number of plants in spring')
    plt.legend()
    plt.show()
   
 
        
