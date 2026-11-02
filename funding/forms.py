from django import forms
from .models import FundingCall


class FundingCallForm(forms.ModelForm):
    class Meta:
        model = FundingCall
        fields = [
            'title',
            'sponsor',
            'description',
            'eligibility',
            'research_area',
            'amount',
            'url',
            'opens_on',
            'deadline',
            'is_published',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. DST SERB Core Research Grant'}),
            'sponsor': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Department of Science & Technology'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'eligibility': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'research_area': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Up to ₹30 Lakhs'}),
            'url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'opens_on': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
