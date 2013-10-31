from django.contrib.admin import SimpleListFilter

class BlastHitsFilter(SimpleListFilter):
    title = 'BLAST hits'
    parameter_name = 'hits'
    
    def lookups(self, request, model_admin):
        return (
            ('none', 'No hits'),
            ('some', 'Hits'),
        )
        
    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.filter(blast_hits__isnull=True)
        else:
            return queryset
