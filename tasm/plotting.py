import math
import numpy as np
import pandas as pd
# import brewer2mpl

from pylab import figure, plot
#from scipy.stats.kde import gaussian_kde
import matplotlib.pyplot as plt

from django.http import HttpResponse
from django.core.exceptions import ImproperlyConfigured
from django.db.models.loading import get_model
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView

from tasm.models import Assembly, Transcript
from tasm.ggstyle import rstyle, rhist


class PlotMixin(object):
    '''
    A mixin that allows matplotlib plotting. Should be used together
    with ListView or DetailView subclasses to get the plotting data
    from the database.
    '''
    format = None

    def make_plot(self):
        '''
        This needs to be implemented in the subclass.
        '''
        pass
    
    def style_plot(self, axes):
        '''
        By default does nothing. May be used to style the plot
        (xkcd, ggplot2, etc).
        '''
        pass
    
    def get_response_content_type(self):
        '''
        Returns plot format to be used in the response.
        '''
        if self.format is not None:
            return 'image/{0}'.format(self.format)
        else:
            raise ImproperlyConfigured('No format is specified for the plot')
        
        
    def render_to_plot(self, context, **response_kwargs):
        response = HttpResponse(
            content_type=self.get_response_content_type()
            )
        fig = self.make_plot()
        fig.savefig(response, format=self.format)
        return response


class TranscriptPlotView(ListView, PlotMixin):
    '''
    A view that outputs various Transcript plots for the given assembly.
    The follwoing plots are produced:
    
        - scatter plot of normalized coverage vs normalized length
        - histogram of normalized coverage of all and best for locus
        transcripts
        - histogram of normalized length of all and best for locus
        transcripts
    '''
    data_fields = ['length', 'coverage',]
    model = Transcript
    format = 'png'
    
    def get_queryset(self):
        self.asm = get_object_or_404(Assembly, pk=int(self.kwargs.get('asm_pk', '')))
        return self.model._default_manager.for_asm(self.asm)
        
    def get_dataframe(self, best=False):
        '''
        Builds a pandas dataframe by retrieving the fields specified
        in self.data_fields from self.queryset.
        '''
        opts = self.model._meta
        fields = [f for f in opts.get_all_field_names() if f in self.data_fields]
        if best:
            values_dict = self.model._default_manager.best_for_asm(self.asm).values(*fields)
        else:
            values_dict = self.model._default_manager.for_asm(self.asm).values(*fields)
        df = pd.DataFrame.from_records(values_dict)
        return df
        
    def make_plot(self):
        
        def _norm_df(df):
            # FIXME: This is silly because hardcodes field names
            max_len = max(df['length'])
            max_cov = max(df['coverage'])
            df['length'] = df['length'] * 100 / max_len
            df['coverage'] = df['coverage'] / max_cov
            return df
            
        def _scatter(ax, df1, df2):
            ax.plot(df1['length'], df1['coverage'], 'o', color='#dc322f', alpha=0.2)
            ax.plot(df2['length'], df2['coverage'], 'o', color='#268bd2', alpha=0.2)
            ax.set_xlabel('Normalized length')
            ax.set_ylabel('Normalized coverage')
            rstyle(ax)
        
        def _hist(ax, df1, df2, col='coverage'):
            defaults = {
                'facecolor': '#268bd2',
                'edgecolor': '#268bd2',
                #'normed': True,
                'alpha': 0.25,
                }
            hist, bins, patches = rhist(ax, df1[col], **defaults)
            defaults.update({'facecolor': '#dc322f', 'edgecolor': '#dc322f',})
            hist, bins, patches = rhist(ax, df2[col], **defaults)
            ax.set_xlabel('Normalized {0}'.format(col))
            ax.set_ylabel('Frequency')
            rstyle(ax)
        
        import matplotlib
        matplotlib.use('Agg')
        
        fig = plt.figure(figsize=(6,18))
        fig.patch.set_alpha(0)
        ax = fig.add_subplot(311)
        
        df_best = _norm_df(self.get_dataframe(best=True))
        df_all = _norm_df(self.get_dataframe())
        
        _scatter(ax, df_all, df_best)
        ax = fig.add_subplot(312)
        _hist(ax, df_best, df_all)
        ax = fig.add_subplot(313)
        _hist(ax, df_best, df_all, col='length')
        return fig
        
    def render_to_response(self, context, **response_kwargs):
        return self.render_to_plot(context, **response_kwargs)
