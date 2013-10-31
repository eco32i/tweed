from django.db import models
from django.db.models import Count
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import View, FormView
from django.views.generic.list import ListView
from django.views.generic.edit import BaseFormView
from django.utils.encoding import smart_str

from tasm.models import Assembly, RefSeq, Contig, Locus, Transcript

ALLOWED_LOOKUPS = ('iexact', 'icontains', 'in', 'gt', 'gte', 'lt',
    'lte', 'istratswith', 'iendswith', 'range', 'isnull', 'iregex')

class HomeView(ListView):
    model = Assembly
    template_name = 'tasm/home.html'
    
    def get_queryset(self):
        qs = super(HomeView, self).get_queryset()
        return qs.annotate(
            num_transcripts=Count('locus__transcript'),
            num_loci=Count('locus', distinct=True),
            num_hits=Count('locus__transcript__blasthit__refseq')
        )
    
    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        stat_dict = {
            'transcripts': Transcript.objects.all().count(),
            'refseqs': RefSeq.objects.all().count(),
            'loci': Locus.objects.all().count(),
            }
        context['stat'] = stat_dict
        return context


class FilteredListView(ListView):
    form_class = None
    
    def __init__(self, *args, **kwargs):
        super(FilteredListView, self).__init__(**kwargs)
        self.filters = kwargs.get('filters', {})
        self.ordering = kwargs.get('order', [])

    def _get_filters(self, request):
        params = request.GET.copy()
        params.pop('page', None)
        params.pop('_filter', None)
        self.ordering = params.pop('o', [])
        opts = self.model._meta
        filters = {}
        # GET parameters from the search form
        for k,v in params.items():
            if not v:
                continue
            kbits = k.split('__')
            #if len(kbits) > 1:
            if kbits[-1] in ALLOWED_LOOKUPS:
                filters.update({smart_str(k): v,})
            else:
                filters.update({smart_str('%s__icontains' % k): v,})
            
            #~ try:
                #~ field, lookup = k.split('__')
                #~ if lookup in ALLOWED_LOOKUPS:
                    #~ filters.update({smart_str(k): v,})
                #~ elif field in opts.get_all_field_names():
                    #~ bits = lookup.split('__')
                    #~ if bits[-1] in ALLOWED_LOOKUPS:
                        #~ filters.update ({smart_str(k): v,})
                    #~ else:
                        #~ filters.update({smart_str('%s__icontains' % k): v,})
            #~ except ValueError:
                #~ filters.update({smart_str('%s__icontains' % k): v,})
        # Parameters from URL
        if 'asm_pk' in self.kwargs:
            if self.model == Transcript:
                asm_key = 'locus__assembly__pk'
            elif self.model == Locus:
                asm_key = 'assembly__pk'
            else:
                asm_key = 'transcript__locus__assembly_id'
            filters.update({asm_key: int(self.kwargs['asm_pk']),})
        return filters

    def get_queryset(self):
        qs = super(FilteredListView, self).get_queryset()
        return qs.filter(**self.filters).distinct().order_by(*self.ordering)
    
    def get_context_data(self,  **kwargs):
        context = super(FilteredListView, self).get_context_data(**kwargs)
        if self.form_class:
            context.update({'form': self.form_class(),})
        if self.filters:
            context.update({'filters': self.filters,})
        return context
        
    def get(self, request, *args, **kwargs):
        # get takes care of initial display and ordering
        if '_clear' in request.GET:
            self.filters.clear()
            self.ordering = []
        else:
            filters = self._get_filters(request)
            self.filters.update(filters)
            #self.ordering = self._get_ordering(request)
        return super(FilteredListView, self).get(request, *args, **kwargs)
