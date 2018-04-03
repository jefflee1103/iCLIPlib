'''
iCLIP_bam2geneprofile.py - produce geneprofile of iCLIP sites
============================================================

:Author:
:Release: $Id$
:Date: |today|
:Tags: Python

Purpose
-------

While bam2geneprofile in CGAT is a very flexible tool, it is not
neccesarily suitable for iCLIP as we should only consider the first
base (or any mutant bases).

This script wraps iCLIP.meta_gene to produce metagene profiles of
iCLIP bam files. It can also use bigwig files - provide either unstranded
data to `--plus-wig` or stranded data by also using `--minus-wig`.

Profiles are always normalised to the sum of each window before summing 
accross windoes, but the full matrix may also be output if custom normalisation
is required.

Using single bases means we don't have to worry about over sampling single
reads, so profiles should be less resolution sensitive

Usage
-----

.. Example use case

Example::

   python iCLIP_bam2geneprofile.py -I geneset.gtf.gz mybam.bam

Type::

   python iCLIP_bam2geneprofile.py --help

for command line help.

Command line options
--------------------

'''

import sys
import os
import CGAT.Experiment as E
import pysam
import CGAT.IOTools as IOTools
import iCLIP.transcript_regions
from itertools import product

sys.path.insert(1, os.path.join(
    os.path.dirname(__file__), ".."))

import iCLIP

regions_dict = {'5flank': transcript_regions.flank5,
                '3flank': transcript_regions.flank3,
                '5UTR' : transcript_regions.UTR5,
                '3UTR' : transcript_regions.UTR3,
                'CDS' : transcript_regions.CDS,
                'first_exon' : transcript_regions.first_exon,
                'middle_exons' : transcript_regions.middle_exons,
                'last_exon' : transcript_regions.last_exon,
                'exons' : transcript_regions.exons,
                'introns' : transcript_regions.introns}

default_bins = {'5flank': 50,
                '3flank': 50,
                '5UTR' : 20,
                '3UTR' : 70,
                'CDS' : 100,
                'first_exon' : 20, 
                'middle_exons' : 100,
                'last_exon' : 70,
                'exons' : 100, 
                'introns' : 100}

def main(argv=None):
    """script main.
    parses command line options in sys.argv, unless *argv* is given.
    """

    if argv is None:
        argv = sys.argv

    # setup command line parser
    parser = E.OptionParser(version="%prog version: $Id$",
                            usage=globals()["__doc__"])

    parser.add_option("-m", "--output-matrix", dest="matrix", type="string",
                      default=None,
                      help="output full matrix to this file")
    parser.add_option("-f", "--flanks-length", dest="flanks", type="int",
                      default=100,
                      help="number of basepairs to use for gene flanks")
    parser.add_option("--pseudo_count", dest="pseudo_count", type="float",
                      default=0,
                      help="add pseduo count to bins to mitiage effects of low numbers of reads")
    parser.add_option("--normalised_profile", dest="normalize_profile", action="store_true",
                      default=False,
                      help="Normlize profile by profile sum")
    parser.add_option("--plus-wig", dest="plus_wig",
                      default=None,
                      help="Use this wig file instead of a BAM file to get clip density"
                      "may be used as only wig file, or may be provided together with"
                      "--minus-wig for standed computation")
    parser.add_option("--minus_wig", dest="minus_wig", default=None,
                      help="Use this to provide stranded wig data")
    parser.add_option("--bed", dest="bedfile", default=None,
                      help="Use bed file with signal instead of bam")
    parser.add_option("--centre", dest="centre", action="store_true",
                      default=False,
                      help="Use centre of read rather than end")
    parser.add_option("--no-gene-norm", dest="row_norm", action="store_false",
                      default=True,
                      help="Do not normalise profile from each gene")
    parser.add_option("--region-length-correction", action="store_true",
                      default=False,
                      help="Correct for regions of different legnths. Calculates something"
                      "akin to an FPKM for the region")
    parser.add_option("-r", "--regions", dest="regions", type="string",
                      default="flank5,exons,flank3",
                      help="Which regions to use. Choose from %s" %
                      ", ".join(region_dict.keys()))
    parser.add_option("-b", "--bins", dest="regions", action="store",
                      default=None,
                      help="Bins to use. If not specified defaults for the"
                      "chosen regions will be used")
    
    
    
    # add common options (-h/--help, ...) and parse command line
    (options, args) = E.Start(parser, argv=argv)

    if options.plus_wig:
        bam = iCLIP.make_getter(plus_wig=options.plus_wig,
                                minus_wig=options.minus_wig)
    elif options.bedfile:
        bam = iCLIP.make_getter(bedfile=options.bedfile)
    else:
        bam = iCLIP.make_getter(bamfile=args[0], centre=options.centre)

    regions_dict['5flanks'] = partial(regions_dict['5flanks'], length=options.flanks)
    regions_dict['3flanks'] = partial(regions_dict['3flanks'], length=options.flanks)

    names = options.regions.split(",")
    regions = [regions_dict[r] for r in names]
    
    if options.bins:
        bins = [int(b) for b in options.bins.split(",")]
        if not len(bins) == len(regions):
            raise ValueError("Bins and regions not same length")
    else:
        bins = [default_bins[r] for r in names]
        
    index = (product([n], range(bins[n])) for n in names)
    
    profile = pandas.Series(
        index=pandas.MultiIndex.from_tuples(index, names = ["region", "region_bin"]))
    accumulator = list()
    
    transcript_interator = GTF.transcript_iterator(GTF.iterator(options.stdin))

    for transcript in transcript_interator:
        this_profile = transcript_meta(transcript, getter, regions, names, bins)

        if options.pseudo_count:
            this_profile = profile.reindex(index, fill_value=0) + pseudo_count

        if row_norm:
            this_profile = this_profile/this_profile.sum()
    
        profile = profile.add(this_profile, fill_value=0)

        if options.matrix:
            profile.name = transcript[0].transcript_id
            accumulator.append(profile)
        
    if options.normalize_profile:
        profile = profile/profile.sum()

    profile.name = "density"
    profile = profile.reset_index()
    profile.index.name = "bin"
    
    profile.to_csv(options.stdout, sep = "\t", index_label="bin")
    
    if options.matrix:
        matrix = pandas.concat(accumulator, axis=1)
        counts_matrix = counts_matrix.transpose()

        counts_matrix = counts_matrix.reset_index(drop=True)
        counts_matrix = counts_matrix.transpose()

        counts_matrix.to_csv(IOTools.openFile(options.matrix, "w"),
                             sep="\t",
                             index=True,
                             index_label="transcript_id")

    # write footer and output benchmark information.
    E.Stop()

if __name__ == "__main__":
    sys.exit(main(sys.argv))