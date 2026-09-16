from django import forms
from .models import CollaborationRequest

class CollaborationRequestForm(forms.ModelForm):
    class Meta:
        model = CollaborationRequest
        fields = ['receiver', 'project', 'message']
        widgets = {
            'receiver': forms.HiddenInput(),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your message here...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if 'receiver' in self.fields:
            self.fields['receiver'].required = False
        if 'project' in self.fields:
            self.fields['project'].required = False
        if user and 'project' in self.fields:
            # Only allow selecting projects the sender is leading
            from projects.models import ResearchProject
            self.fields['project'].queryset = ResearchProject.objects.filter(leader=user)

