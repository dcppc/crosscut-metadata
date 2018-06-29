#!/bin/tcsh

setenv PYTHONPATH ./

# Generate sample/subject histogram for _all_ samples
./bin/gtex_v7_to_dats.py --print_sample_histogram > all-histogram.txt
# And RNA-Seq only
./bin/gtex_v7_to_dats.py --print_sample_histogram --smafrze=RNASEQ > rnaseq-histogram.txt
