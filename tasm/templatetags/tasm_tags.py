from django import template
from django.core.urlresolvers import reverse
from django.template.context import Context
from django.utils.safestring import mark_safe
from django.utils.http import urlencode
from django.utils.html import conditional_escape

from monoseq import pprint_sequence, HtmlFormat

from tasm.models import Transcript

register = template.Library()

@register.filter(is_safe=True)
def transcript_filter(key):
    bits = key.split('__')
    if bits[-1] == 'gte':
        bits[-1] = u'\u2265'
    elif bits[-1] == 'lt':
        bits[-1] = '<'
    return ' '.join(bits)
transcript_filter.is_safe = True
    
    
@register.simple_tag(takes_context=True)
def render_tabs(context, active):
    tab_views = (
        ('tasm_transcripts_for_asm_view', 'Transcripts'),
        ('tasm_transcript_plots_view', 'Plots'),
        )
    tab_item_tpl = '<li{css}><a href="{url}">{text}</a></li>'
    lines = []
    for view,text in tab_views:
        if view == active:
            url = '#'
            css = ' class="active"'
        else:
            url = reverse(view, kwargs=dict(asm_pk=int(context['view'].kwargs['asm_pk'])))
            css = ''
        lines.append(tab_item_tpl.format(
            css=css,
            url=url,
            text=text)
            )
    return ''.join(lines)


@register.filter(needs_autoescape=True)
def pretty_seq(seq, autoescape=None):
    # This is how it's done in the docs but this ain't working
    # Wonder why.
    #~ if autoescape:
        #~ esc = conditional_escape
    #~ else:
        #~ esc = lambda x: x
    #~ result = esc(pprint_sequence(seq, blocks_per_line=6, format=HtmlFormat))
    return mark_safe(pprint_sequence(seq, blocks_per_line=6, format=HtmlFormat))
pretty_seq.is_safe = True

@register.filter(is_safe=True)
def best_length(locus):
    return Transcript.objects.best_for_locus(locus).length

@register.filter(is_safe=True)
def best_coverage(locus):
    return Transcript.objects.best_for_locus(locus).coverage

@register.simple_tag
def blast_hit_link(hit):
    url = hit.get_absolute_url()
    link_text = hit.accession
    return '<a href="{url}">{text} </a>'.format(url=url, text=link_text)

@register.inclusion_tag('tasm/includes/th_sort.html', takes_context=True)
def sort_by(context, field, text):
    request = context['request']
    params = request.GET.copy()
    ordering = params.pop('o', [])
    url_param = field
    css = 'sorting'
    if ordering:
        o = ordering[0]
        if o.startswith('-') and o.endswith(field):
            css = 'sorting-asc'
        elif o == field:
            css = 'sorting-desc'
            url_param = '-%s' % field
    return {
        'css': css,
        'href': '?%s' % urlencode({'o': url_param,}),
        'link': text,
        }

@register.inclusion_tag('tasm/includes/crumbs.html', takes_context=True)
def crumbs(context):
    request = context['request']
    bits = request.path.strip('/').split('/')
    return { 'crumbs': bits,}
    
