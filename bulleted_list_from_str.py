# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 13:47:10 2025

@author: cariefrantz

Takes a list of strings like the one below...
"'chl','phaeo','FoFa','PAM','diatom_ct','phyto_ct_all','phyto_ct_select'"

...and generates a bulleted list like this:
- chl
- phaeo
- FoFa
- PAM
- diatom_ct
- phyto_ct_all
- phyto_ct_select
- phyto_ct_other
"""

def makeList(param_str):
    # Split the string into individual items and remove surrounding quotes
    params = [p.strip().strip("'") for p in param_str.split(',')]
    
    # Print as a bulleted list
    for param in params:
        print(f"- {param}")