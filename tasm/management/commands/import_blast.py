import os
from optparse import make_option
from Bio.Blast import NCBIXML

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from tasm.models import Assembly, Transcript, Locus, RefSeq, BlastHit, BASE_REFSEQ_URL


class Command(BaseCommand):
    '''
    Imports results of the local blast run on assembly's transcripts.fa
    file.
    '''
    option_list = BaseCommand.option_list + (
        make_option('--asm', default='', dest='asm',
            help='Assembly'),
        make_option('--expect', default='1e-4', dest='expect',
            help='Expect value cutoff'),
        make_option('--max_hits', default='1', dest='max_hits',
            help='Maximum number of hits to import per transcript'),
        )
    args = '<blastout.xml>'
    refseqs = []
    blasthits = []
    
    def set_options(self, **options):
        '''
        Set instance variables based on options dict
        '''
        try:
            self.max_hits = int(options['max_hits'])
        except ValueError:
            raise CommandError('max_hits must be integer.')
        try:
            self.expect = float(options['expect'])
        except ValueError:
            raise CommandError('Expect value must be float.')
        try:
            self.asm = Assembly.objects.get(identifier=options['asm'])
        except ObjectDoesNotExist:
            raise CommandError('Unknown assembly: {asm}.'.format(asm=options['asm']))

    def _import_blast_record(self, record):
        '''
        Handles import of a single BLAST record. Adds records to
        self.refseqs and self.blasthits to be used in bulk_create
        later.
        
        RefSeq instances are created as needed.
        BlastHit instances are created in bulk in self.handle()
        '''
        if not record.alignments:
            return
        query_bits = record.query.split('_')
        locus = Locus.objects.get(locus_id=int(query_bits[1]), assembly=self.asm)
        transcript = Transcript.objects.get(
            locus=locus, 
            transcript_id=int(query_bits[3].split('/')[0]))
        i = 0
        while i < self.max_hits:
            # FIXME: This is slow because it hits the database (almost)
            # every iteration. Needs to be improved, not clear how.
            aln = record.alignments[i]
            refseq, created = RefSeq.objects.get_or_create(accession=aln.accession,
                defaults={
                    'definition': aln.hit_def,
                    'length': aln.length,
                    'url': BASE_REFSEQ_URL + aln.accession
                })
            self.refseqs.append(refseq)
            best_hsp = aln.hsps[0]
            self.blasthits.append(BlastHit(
                transcript=transcript,
                refseq=refseq,
                align_length=best_hsp.align_length,
                identities=best_hsp.identities,
                expect=best_hsp.expect,
                score=best_hsp.score
            ))
            i += 1

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Invalid number of arguments.')
        blast_file = args[0]
        if not os.path.exists(blast_file):
            raise CommandError('File {file} not found.'.format(file=blast_file))
        self.set_options(**options)
        self.stdout.write('Importing BLAST results for assembly %s ...' % self.asm)
        with open(blast_file, 'rU') as fi:
            for rec in NCBIXML.parse(fi):
                self._import_blast_record(rec)
        self.stdout.write('Accepted {hits} for {seqs} sequences.'.format(
            hits=len(self.blasthits),
            seqs=len(self.refseqs)
            ))
        self.stdout.write('Importing BLAST hits ...')
        BlastHit.objects.bulk_create(self.blasthits)
        self.stdout.write('DONE.')
