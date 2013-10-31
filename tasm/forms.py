from django import forms

# Form field names are directly used to filter queryset in the view
# Ugly but works for now.

class TranscriptFilterForm(forms.Form):
    length__gte = forms.DecimalField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'min length...'}))
    length__lt = forms.DecimalField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'max length...'}))
    coverage__gte = forms.DecimalField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'min coverage...'}))
    coverage__lt = forms.DecimalField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'max coverage...'}))

class LociFilterForm(forms.Form):
    transcript__length__gt = forms.DecimalField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'min length...'}))
    transcript__coverage__gt = forms.DecimalField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'min coverage...'}))


class RefSeqFilterForm(forms.Form):
    definition = forms.CharField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'definition...'}))
    accession = forms.CharField(required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-medium',
            'placeholder': 'accession...'}))
