from django.db import models
from django.contrib import admin

from tasm.models import Assembly, Locus, Contig, Stat, Transcript, RefSeq
from tasm.filters import BlastHitsFilter
admin.autodiscover()

class AssemblyAdmin(admin.ModelAdmin):
    model = Assembly
    list_display = ('species', 'identifier', 'k_min', 'k_max',)
    
admin.site.register(Assembly, AssemblyAdmin)


class LocusAdmin(admin.ModelAdmin):
    model = Locus
    list_display = (
        'assembly',
        'locus_id',
        'num_transcripts',
        'best_transcript_length',
        'best_transcript_coverage'
        )
    list_filter = ('assembly__identifier',)
    
    def num_transcripts(self, obj):
        return len(obj.transcript_set.all())
    num_transcripts.short_description = 'Number of transcripts'
    
    def best_transcript_length(self, obj):
        return Transcript.objects.best_for_locus(obj).length
    best_transcript_length.short_description = 'Best transcript length'
    
    def best_transcript_coverage(self, obj):
        return Transcript.objects.best_for_locus(obj).coverage
    best_transcript_coverage.short_description = 'Best transcript coverage'
    
admin.site.register(Locus, LocusAdmin)


class TranscriptAdmin(admin.ModelAdmin):
    model = Transcript
    list_display = (
        'locus',
        'transcript_id',
        'sequence',
        'length',
        'confidence',
        'coverage',
        )
    list_filter = ('locus__assembly__identifier', BlastHitsFilter)

    #~ def wrapped_sequence(self, obj):
        #~ seq = ''
        #~ i = 1
        #~ while i*50
admin.site.register(Transcript, TranscriptAdmin)


class RefSeqAdmin(admin.ModelAdmin):
    model = RefSeq
    list_display = ('accession', 'definition', 'length', 'num_hits',)
    search_fields = ('accession', 'definition',)
    
    def num_hits(self, obj):
        return obj.transcript_set.count()
    num_hits.short_description = 'Number of transcripts'

admin.site.register(RefSeq, RefSeqAdmin)
