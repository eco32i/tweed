from django.db import models
from django.db.models import Min, Max

BASE_REFSEQ_URL = 'http://www.ncbi.nlm.nih.gov/nuccore/'

class Assembly(models.Model):
    '''
    Container class to hold loci and transcripts from a single
    assembly.
    '''
    species = models.CharField('Species', max_length=100, default='unknown')
    identifier = models.CharField('Assembly ID', max_length=50, unique=True)
    k_min = models.PositiveIntegerField('K min')
    k_max = models.PositiveIntegerField('K max')
    
    class Meta:
        verbose_name_plural = 'assemblies'

    def __unicode__(self):
        return self.identifier
    
    @models.permalink
    def get_absolute_url(self):
        return ('tasm_loci_for_asm_view', None, {'asm_pk': self.pk})


class Locus(models.Model):
    '''
    Locus. Transcripts grouped into one locus may or may not originate
    from the same genetic locus.
    '''
    locus_id = models.PositiveIntegerField('Locus id', db_index=True)
    assembly = models.ForeignKey(Assembly)
    
    class Meta:
        unique_together = (('locus_id', 'assembly',),)
        verbose_name_plural = 'loci'
        ordering = ('locus_id',)

    def __unicode__(self):
        return '{asm}:Locus [{loc}]'.format(asm=self.assembly, loc=self.locus_id)
    
    @models.permalink
    def get_absolute_url(self):
        return ('tasm_locus_view', None, {'pk': self.pk,})


class Contig(models.Model):
    '''
    Populated from contigs.fa file. This file is FASTA format and 
    contains all nodes in the form:
        >NODE_45_length_92_cov_13.978261
        TTCTCTTCCTGCTGCTACTGAGATGTTTCAATTCACAGCGTGTCTCTTCATTCGACTATG
        TATTCATCGATATGATAATTGAGGATTAGCTCAATTAGGTTTCCCCATTCGGAAATCc
    Contains only contigs longer than 2k?
    '''
    # This should probably be a ForeignKey to Nodes table
    node_id = models.PositiveIntegerField('NODE ID', db_index=True)
    length = models.PositiveIntegerField('Length')
    coverage = models.FloatField('Coverage')
    sequence = models.TextField('Sequence')
    assembly = models.ForeignKey(Assembly)
    
    class Meta:
        ordering = ('node_id',)


class Stat(models.Model):
    '''
    Populated from stats.txt file
    Only process length and long_cov for now.
    length is given in k-mers.
    
    PS Probably should be renamed Node
    '''
    # TODO: This should probably be renamed Node, but then again
    # not every node will have associated sequence!
    node_id = models.PositiveIntegerField('NODE ID', db_index=True)
    length = models.PositiveIntegerField('Length')
    coverage = models.FloatField('Coverage')
    assembly = models.ForeignKey(Assembly)
    
    class Meta:
        ordering = ('node_id',)


class RefSeq(models.Model):
    '''
    Reference sequence from NCBI database
    '''
    accession = models.CharField('Accession number', max_length=50, unique=True, db_index=True)
    definition = models.TextField('Definition')
    length = models.PositiveIntegerField('Length')
    url = models.URLField('URL to the sequence', max_length=200)
    
    class Meta:
        ordering = ('accession',)
        verbose_name = 'reference seqeunce'
        verbose_name_plural = 'reference sequences'

    def __unicode__(self):
        return self.accession
        
    def save(self, *args, **kwargs):
        if not self.pk and not self.url:
            self.url = BASE_REFSEQ_URL + self.accession
        return super(RefSeq, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('tasm_refseq_view', None, {'accession': self.accession,})


class TranscriptManager(models.Manager):
    
    def for_locus(self, loc):
        '''
        Gets a set of transcripts for the given locus (as instance, pk, 
        or string).
        '''
        if isinstance(loc, Locus):
            return self.get_query_set().filter(locus=loc)
        elif isinstance(loc, int):
            return self.get_query_set().filter(locus__pk=loc)
        elif isinstance(loc, str):
            return self.get_query_set().filter(locus__pk=int(loc))
            
    def best_for_locus(self, loc, percent_cutoff=15):
        qs = self.for_locus(loc)
        if qs.count() > 6:
            loc_data = qs.aggregate(Min('length'), Max('length'))
            cutoff = loc_data['length__min'] + (loc_data['length__max'] - loc_data['length__min']) / 100 * percent_cutoff
            return qs.filter(length__gt=cutoff).order_by('-coverage')[0]
        else:
            return qs.order_by('-coverage')[0]


class Transcript(models.Model):
    '''
    Populated from transcripts.fa file. This file contains transcripts
    grouped by locus. Every transcript in a locus is assigned a 
    confidence score. The file is FASTA formst and contains records of 
    the form:
        >Locus_1_Transcript_5/59_Confidence_0.009_Length_195
        GTCGGCTACCCACCCGGCCCGTCTGTGAACACGGACCAAGGAGTCTAACGACATGTGTGC
        GAGTCAACGGGCGAGTAAACCCGTAAGGCGCAAGGAAGCTGATTGGCGGGATCCCTCGCG
        GGTTGCACCGCCGACCGACCCTGATCTTCTGTGAAGGGTTCGAGTTGGAGCACACCTGTC
        GGGACCCGAAAGATG
    '''
    locus = models.ForeignKey(Locus, null=True, blank=True)
    transcript_id = models.PositiveIntegerField('Transcript ID', db_index=True)
    confidence = models.FloatField('Confidence')
    length = models.PositiveIntegerField('Length')
    sequence = models.TextField('Sequence')
    coverage = models.FloatField('Coverage')
    
    blast_hits = models.ManyToManyField('RefSeq', through='BlastHit')
    
    objects = TranscriptManager()

    class Meta:
        unique_together = (('locus', 'transcript_id',),)
        ordering = ('locus', 'transcript_id',)

    def __unicode__(self):
        return '{loc}:{trans} ({length})'.format(
            loc=self.locus,
            trans=self.transcript_id,
            length=self.length
            )

    @models.permalink
    def get_absolute_url(self):
        return ('tasm_transcript_view', None, {'pk': self.pk,})


class BlastHit(models.Model):
    '''
    Intermediate table for many-to-many relationship between 
    Transcript and RefSeq.
    '''
    transcript = models.ForeignKey(Transcript)
    refseq = models.ForeignKey(RefSeq)
    align_length = models.PositiveIntegerField('Alignment length')
    identities = models.PositiveIntegerField('Identical')
    expect = models.FloatField('Expect value')
    score = models.FloatField('Score')
    
    def __unicode__(self):
        return '{asm}:{t} -- {seq}'.format(
            asm=self.transcript.assembly,
            t=self.transcript,
            seq=self.refseq
            )
