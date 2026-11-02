import re
from django import forms
from django.core.exceptions import ValidationError
from .models import ResearcherProfile, ResearchInterest, Skill, Department


def validate_orcid_checksum(orcid_str: str) -> bool:
    """
    Validates an ORCID iD using ISO 7064 MOD 11-2.
    Format: 0000-0002-1825-0097 (16 chars in 4 hyphen-separated blocks).
    """
    if not orcid_str:
        return True
    val = orcid_str.strip()
    if not re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', val):
        return False

    digits = val.replace('-', '')
    base = digits[:15]
    check = digits[15].upper()

    total = 0
    for d in base:
        total = (total + int(d)) * 2
    remainder = total % 11
    result = (12 - remainder) % 11
    expected = 'X' if result == 10 else str(result)
    return check == expected


class ResearcherProfileForm(forms.ModelForm):
    class Meta:
        model = ResearcherProfile
        fields = [
            'department',
            'headline',
            'expertise_summary',
            'google_scholar_url',
            'orcid_id',
            'scopus_id',
            'years_experience',
            'is_available_for_collaboration'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'headline': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. AI Researcher at X University'}),
            'expertise_summary': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'google_scholar_url': forms.URLInput(attrs={'class': 'form-input'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '0000-0002-1825-0097'}),
            'scopus_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 57200000000'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'is_available_for_collaboration': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_orcid_id(self):
        orcid_id = self.cleaned_data.get('orcid_id', '').strip()
        if orcid_id:
            if not validate_orcid_checksum(orcid_id):
                raise ValidationError("Enter a valid ORCID iD, like 0000-0002-1825-0097.")
        return orcid_id


class ResearchInterestForm(forms.ModelForm):
    class Meta:
        model = ResearchInterest
        fields = ['name', 'category', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.TextInput(attrs={'class': 'form-input'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
