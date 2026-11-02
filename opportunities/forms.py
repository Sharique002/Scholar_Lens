from django import forms
from .models import ResearchOpening, OpportunityApplication


class ResearchOpeningForm(forms.ModelForm):
    class Meta:
        model = ResearchOpening
        fields = ['title', 'project', 'department', 'description', 'required_skills', 'spots_available', 'deadline', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Research Assistant in NLP'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe duties, qualifications, and project background...'}),
            'required_skills': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'spots_available': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class OpportunityApplicationForm(forms.ModelForm):
    class Meta:
        model = OpportunityApplication
        fields = ['statement', 'cv_pdf']
        widgets = {
            'statement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain your relevant coursework, experience, and motivation...'
            }),
            'cv_pdf': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,application/pdf'
            }),
        }
