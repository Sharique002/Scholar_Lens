from django import forms
from .models import FundingCall, FundingApplication


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


class FundingApplicationForm(forms.ModelForm):
    class Meta:
        model = FundingApplication
        fields = ['title', 'project', 'amount_requested', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Proposal Title'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 1500000.00'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Proposal summary, co-investigators, etc.'}),
        }
