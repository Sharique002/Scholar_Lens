from django import forms
from papers.models import ResearchPaper

class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search papers...',
            'aria-label': 'Search'
        })
    )
    research_area = forms.ChoiceField(
        choices=[('', 'All Research Areas')] + ResearchPaper.ResearchArea.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Year (e.g. 2024)',
            'min': 1950,
            'max': 2100
        })
    )
    author = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Author name...',
        })
    )
    threshold = forms.FloatField(
        required=False,
        min_value=0.0,
        max_value=100.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min score % (e.g. 50)',
            'step': '5'
        })
    )
    semantic = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Use Semantic Ranking'
    )
