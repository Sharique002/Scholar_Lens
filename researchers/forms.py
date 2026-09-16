from django import forms
from .models import ResearcherProfile, ResearchInterest, Skill

class ResearcherProfileForm(forms.ModelForm):
    class Meta:
        model = ResearcherProfile
        fields = [
            'headline', 'expertise_summary', 'google_scholar_url', 
            'orcid_id', 'years_experience', 'is_available_for_collaboration'
        ]
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AI Researcher at X University'}),
            'expertise_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'google_scholar_url': forms.URLInput(attrs={'class': 'form-control'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000-0000-0000-0000'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available_for_collaboration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ResearchInterestForm(forms.ModelForm):
    class Meta:
        model = ResearchInterest
        fields = ['name', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
