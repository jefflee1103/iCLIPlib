''' This a modeule that holds functions and classes useful for analysing iCLIP data '''

from counting import count_intervals, count_transcript, countChr
from utils import spread, rand_apply, randomiseSites, TranscriptCoordInterconverter
from meta import meta_gene
from kmers import pentamer_enrichment, pentamer_frequency
from distance import calcAverageDistance, findMinDistance, corr_profile

