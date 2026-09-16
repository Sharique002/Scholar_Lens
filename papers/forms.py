from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import ResearchPaper, PaperAuthor


class PaperUploadForm(forms.ModelForm):
    class Meta:
        model = ResearchPaper
        fields = ['title', 'abstract', 'research_area', 'keywords', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter paper title'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter paper abstract'}),
            'research_area': forms.Select(attrs={'class': 'form-control'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Machine Learning, Neural Networks'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'})
        }

    def clean_pdf_file(self):
        file = self.cleaned_data.get('pdf_file')
        if file:
            # Check file extension
            if not file.name.lower().endswith('.pdf'):
                raise ValidationError("Only PDF files are allowed.")
            
            # Check content type
            if file.content_type != 'application/pdf':
                raise ValidationError("Invalid file type. Only PDF is accepted.")
            
            # Check file size
            max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024) # Default 10MB
            if file.size > max_size:
                raise ValidationError(f"File size must be under {max_size / (1024 * 1024)} MB.")
                
        return file


class PaperEditForm(forms.ModelForm):
    class Meta:
        model = ResearchPaper
        fields = ['title', 'abstract', 'research_area', 'keywords']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'research_area': forms.Select(attrs={'class': 'form-control'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control'})
        }


class PaperAuthorForm(forms.ModelForm):
    class Meta:
        model = PaperAuthor
        fields = ['name', 'email', 'affiliation', 'is_corresponding']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (optional)'}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Affiliation (optional)'}),
            'is_corresponding': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


PaperAuthorFormSet = inlineformset_factory(
    ResearchPaper,
    PaperAuthor,
    form=PaperAuthorForm,
    extra=3,
    can_delete=True
)
