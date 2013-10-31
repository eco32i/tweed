import os, csv
from optparse import make_option
from Bio import SeqIO

from django.core.management.base import BaseCommand, CommandError

from tasm.models import Assembly, Contig, Stat, Transcript, Locus
from tasm.utils import get_contig_ids

CONTIG_FILE = 'contigs.fa'
CONTIGORDERING_FILE = 'contig-ordering.txt'
STATS_FILE = 'stats.txt'
TRANSCRIPTS_FILE = 'transcripts.fa'
    
class Command(BaseCommand):
    '''
    Imports the files produced by oases pipeline.
    Files are assumed to be .tsv with the first line as header.
    The order of processing is as follows:
        - first assembly instance is created from options passed in to
        the command
        - the Contig table is populated from contig.fa file
        - the Stat table is populated from stats.txt file
        - the trancripts.fa is processed setting up the Locus table and
        calculating each transcript coverage by examining the trancript
        composition in contig-ordering.txt and pulling in the coverage
        info for each contig from the Stat table.
    '''
    option_list = BaseCommand.option_list + (
        make_option('--species', default='', dest='species',
            help='Species'),
        make_option('--k-min', default='', dest='k_min',
            help='K min'),
        make_option('--k-max', default='', dest='k_max',
            help='K max'),
        make_option('--dir', default='', dest='dir',
            help='oases output directory'),
        )
    args = '<assembly identifier>'
    
    def set_options(self, **options):
        '''
        Set instance variables based on options dict
        '''
        dir = options['dir']
        if os.path.exists(dir):
            self.dir = dir
        else:
            raise CommandError('Directory %s does not exist.' % dir)
        try:
            k_min = int(options['k_min'])
            k_max = int(options['k_max'])
        except ValueError:
            raise CommandError('k_min and k_max must be integers.')
        if k_max > k_min:
            self.k_min = k_min
            self.k_max = k_max
        else:
            raise CommandError('k_max must be greater than k_min.')
        self.species = options['species']

    def create_asm(self, id):
        asm, created = Assembly.objects.get_or_create(
            identifier=id,
            k_min=self.k_min,
            k_max=self.k_max
            )
        if created:
            self.asm = asm
        else:
            raise CommandError('Assembly identifier must be unique')
            
    def import_contigs(self):
        '''
        contigs.fa is just a FASTA file so we use biopython's parser
        to handle it
        '''
        contig_fname = os.path.join(self.dir, CONTIG_FILE)
        contigs = []
        with open(contig_fname, 'rU') as fi:
            for rec in SeqIO.parse(fi, 'fasta'):
                # TODO: Need to check here for a bad header!
                bits = rec.id.split('_')
                contigs.append(Contig(
                    assembly=self.asm,
                    sequence=rec.seq,
                    node_id=bits[1],
                    length=bits[3],
                    coverage=bits[5]
                ))
        return Contig.objects.bulk_create(contigs)

    def import_stats(self):
        import csv
        stats_filename = os.path.join(self.dir, STATS_FILE)
        stats = []
        with open(stats_filename, 'rU') as fi:
            reader = csv.DictReader(fi, delimiter='\t')
            for rec in reader:
                if rec['long_cov'] != 'Inf':
                    stats.append(Stat(
                        assembly=self.asm,
                        node_id=rec['ID'],
                        length=rec['lgth'],
                        coverage=rec['long_cov']
                    ))
        return Stat.objects.bulk_create(stats)

    def _build_contig_ordering(self):
        '''
        Parses contig-ordering.txt file as a FASTA file and builds a
        list of tuples where the first element is locus id, the second
        is the transcript id and the third value is the list of
        node ids for the transcript.
        '''
        filename = os.path.join(self.dir, CONTIGORDERING_FILE)
        contigs = []
        self.stdout.write('Processing %s ...' % CONTIGORDERING_FILE)
        with open(filename, 'rU') as fi:
            for rec in SeqIO.parse(fi, 'fasta'):
                bits = rec.id.split('_')
                # Only process records that correspond to a reported
                # transcripts
                if 'Transcript' in bits:
                    contigs.append((
                        int(bits[1]),
                        int(bits[3].split('/')[0]),
                        get_contig_ids(rec.seq),
                    ))
        return contigs

    def _compute_coverage(self, contig_ids):
        '''
        Computes the coverage of the transcript made up from contig_ids
        as a geometric mean of the coverage for each contig.
        '''
        from scipy.stats import gmean
        filter = {'assembly': self.asm, 'node_id__in': contig_ids,}
        values = Stat.objects.filter(**filter).values_list('coverage', flat=True)
        return gmean(values)

    def process_transcripts(self):
        '''
        transcripts.fa is a FASTA file so we use biopython's
        fasta parser to handle it.
        
        This only hits database three times.
        '''
        filename = os.path.join(self.dir, TRANSCRIPTS_FILE)
        transcripts = []
        loci = []
        contig_ordering = self._build_contig_ordering()
        self.stdout.write('Importing transcripts and calculating coverage...')
        with open(filename, 'rU') as fi:
            # Parse through fasta file, create loci and transcripts
            # Compute coverage for transcripts
            for i, rec in enumerate(SeqIO.parse(fi, 'fasta')):
                # TODO: check for a bad header!
                bits = rec.id.split('_')
                loci.append(int(bits[1]))
                transcripts.append(dict(
                    locus=int(bits[1]),
                    transcript_id=int(bits[3].split('/')[0]),
                    confidence=bits[5],
                    length=bits[7],
                    sequence=rec.seq,
                    coverage=self._compute_coverage(contig_ordering[i][2])
                ))
        self.stdout.write('Done calculating coverage...')
        created_loci = Locus.objects.bulk_create([Locus(locus_id=loc_id, assembly=self.asm) for loc_id in set(loci)])
        self.stdout.write('...\tProcessed %d loci ...' % len(created_loci))
        # Assign appropriate locus pk values to matching transcripts
        loci = Locus.objects.filter(assembly=self.asm).values_list('pk', 'locus_id')
        for t in transcripts:
            for pk, loc_id in loci:
                if t['locus'] == loc_id:
                    del t['locus']
                    t['locus_id'] = pk
                    break
        return Transcript.objects.bulk_create([Transcript(**kwargs) for kwargs in transcripts])
        

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Invalid number of arguments.')
        self.set_options(**options)
        self.stdout.write('Creating new assembly ...')
        self.create_asm(args[0])
        self.stdout.write('Populating Contig table ...')
        n = self.import_contigs()
        self.stdout.write('...\tImported %d contigs ...' % len(n))
        self.stdout.write('Populating Stat table ...')
        n = self.import_stats()
        self.stdout.write('...\tImported %d nodes ...' % len(n))
        self.stdout.write('Processing transcripts ...')
        n = self.process_transcripts()
        self.stdout.write('...\tProcessed %d transcripts ...' % len(n))
        self.stdout.write('DONE.')
