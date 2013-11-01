tweed
=====

Database to store and analyze the results of oases de novo
assembly pipeline. The database is built by parsing the following 
files from the standard ``oases`` output:

   - stats.txt
   - contig-ordering.txt
   - transcripts.fa

The resulting transcripts are annotated with coverage informations
computed as geometric mean of the nodes covering the tranascript.

If ``transcripts.fa`` is blasted against a genome of interest, the
resulting .xml output file can be imported to annotate transcripts that
produced blast hits.

Dependencies
===========

    - django
    - django-pagination
    - gunicorn
    - scipy
    - monoseq
    - biopython
 
TODO
====

   - views: by assembly, by locus, best transcript in locus
   - blast annotations for transcripts
   - plotting
