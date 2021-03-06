tweed
=====

A database to store and analyze the results of oases *de novo*
assembly pipeline. Inspired by [oases2csv](https://code.google.com/p/oases-to-csv/wiki/oases2csvwiki). 
The database is built by parsing the following files from the standard ``oases`` output:

   - stats.txt
   - contig-ordering.txt
   - transcripts.fa

The resulting transcripts are annotated with coverage information
calculated as geometric mean of the nodes comprising the tranascript and
grouped by loci.

The best transcript in the locus is selected as the transcript in top 20%
by length having the maximum coverage.

If ``transcripts.fa`` is blasted against a genome of interest, the
resulting .xml output file can be imported to annotate transcripts that
produced blast hits.

Dependencies
============

- [django](http://www.djangoproject.com)
- [django-pagination](https://github.com/ericflo/django-pagination.git)
- [gunicorn](http://gunicorn.org)
- [scipy](http://www.scipy.org/)
- [monoseq](https://github.com/martijnvermaat/monoseq)
- [biopython](http://biopython.org)
- [matplotlib](http://matplotlib.org)
 
TODO
====

   - views: by assembly, by locus, best transcript in locus
   - blast annotations for transcripts
   - tunable length cutoff for the best in locus transcript selection
