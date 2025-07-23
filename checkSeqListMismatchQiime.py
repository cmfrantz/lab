# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 09:30:52 2025

@author: cariefrantz

This script checks for mismatches between feature tables (ASV-table) and
sequence lists (rep-seq) to make sure that everything in the feature table
is also present in rep-seq. It prints any feature IDs that are present in
the feature table but not in rep-seq.

It requires that qiime2 be installed in the active conda environment.
"""

# Imports
import qiime2
import pandas as pd

# Filepaths of the files to compare
table_fp = "mypath/feature-table.qza"
seqs_fp = "mypath/rep-seq.qza"

# Load the tables from the qza files
table_artifact = qiime2.Artifact.load(table_fp)
seqs_artifact = qiime2.Artifact.load(seqs_fp)

table_df = table_artifact.view(pd.DataFrame)
seqs_srs = seqs_artifact.view(pd.Series)

# Grab the feature ids
table_ids = set(table_df.columns)
seqs_ids = set(seqs_srs.index)

# Determine feature ids in feature-table that are not in rep-seq
difference = table_ids.difference(seqs_ids)

# Print the results
print("The feature table contains " + str(len(table_ids)) + " features."
      + "\nThe rep-seq list contains " + str(len(seqs_ids)) + " features."
      + "\nThere are " + str(len(difference)) + " features in the feature table that are not present in the rep-seq file:"
      )
print(*list(difference), sep = "\n")