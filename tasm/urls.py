from django.conf.urls import patterns, url
from django.views.generic.detail import DetailView

from tasm import views
from tasm.models import RefSeq, Locus, Transcript
from tasm.forms import TranscriptFilterForm, RefSeqFilterForm

#
# URL for transcripts:
#   /asm/<asm_pk>/loci - loci for the asssembly
#   /asm/<asm_pk>/transcripts - transcripts for the asssembly
#   /asm/<asm_pk>/hits - refseqs of BLAST hits for the assembly
#
#   /loci/<locus_pk> - individual locus
#       - also shows all transcripts for that locus
#   /transcripts/<transcript_pk> - individual transcript
#       - also shows all BLAST hits for that transcript
#   /refseqs/<accession> - individual refseq
#       - also shows all transcripts that have BLAST hits on that refseq

urlpatterns = patterns('',
    url(r'^$', views.HomeView.as_view(), name='tasm_home_view'),
    
    url(r'^refseqs/$', views.FilteredListView.as_view(
        model=RefSeq,
        template_name='tasm/refseq_list.html',
        form_class=RefSeqFilterForm
        ), name='tasm_refseq_list_view'),
        
    url(r'^asm/(?P<asm_pk>\d+)/loci/$', views.FilteredListView.as_view(
        model=Locus,
        template_name='tasm/loci_list.html'
        ), name='tasm_loci_for_asm_view'),
    url(r'^asm/(?P<asm_pk>\d+)/transcripts/$', views.FilteredListView.as_view(
        model=Transcript,
        template_name='tasm/trasncript_list.html',
        form_class=TranscriptFilterForm
        ), name='tasm_transcripts_for_asm_view'),
    url(r'^asm/(?P<asm_pk>\d+)/hits/$', views.FilteredListView.as_view(
        model=RefSeq,
        template_name='tasm/refseq_list.html',
        form_class=RefSeqFilterForm
        ), name='tasm_refseqs_for_asm_view'),
        
    url(r'^loci/(?P<pk>\d+)/$', DetailView.as_view(
        model=Locus,
        template_name='tasm/locus.html',
        context_object_name='locus'), name='tasm_locus_view'),
    url(r'^refseqs/(?P<accession>\w+)/$', DetailView.as_view(
        model=RefSeq,
        slug_field='accession',
        slug_url_kwarg='accession',
        template_name='tasm/refseq.html',
        context_object_name='refseq'), name='tasm_refseq_view'),
    url(r'^transcripts/(?P<pk>\d+)/$', DetailView.as_view(
        model=Transcript,
        template_name='tasm/transcript_list.html',
        context_object_name='locus'), name='tasm_transcript_view'),
)
