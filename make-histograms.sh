#!/bin/tcsh

# Generate sample/subject histogram for _all_ samples
./gtex_v7_to_dats.py --print_sample_histogram 
# And RNA-Seq only
./gtex_v7_to_dats.py --print_sample_histogram --smafrze=RNASEQ
