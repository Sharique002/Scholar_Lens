from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import ResearchProject, ProjectMember, Milestone


class ProjectForm(forms.ModelForm):
    class Meta:
        model = ResearchProject
        fields = ['title', 'description', 'research_area', 'status', 'start_date', 'end_date', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'research_area': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProjectMemberForm(forms.ModelForm):
    class Meta:
        model = ProjectMember
        fields = ['user', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = [
            'title',
            'is_deliverable',
            'owner',
            'start_date',
            'due_date',
            'status',
            'progress',
            'depends_on',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Complete Phase 1 Dataset'}),
            'is_deliverable': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'progress': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 100}),
            'depends_on': forms.SelectMultiple(attrs={'class': 'form-select', 'style': 'min-height: 100px;'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.project = project
        elif self.instance and hasattr(self.instance, 'project') and self.instance.project_id:
            self.project = self.instance.project
        else:
            self.project = None

        if self.project:
            member_ids = list(self.project.members.values_list('user_id', flat=True))
            if self.project.leader_id and self.project.leader_id not in member_ids:
                member_ids.append(self.project.leader_id)
            self.fields['owner'].queryset = User.objects.filter(id__in=member_ids)
            self.fields['depends_on'].queryset = Milestone.objects.filter(project=self.project)
        else:
            self.fields['owner'].queryset = User.objects.none()
            self.fields['depends_on'].queryset = Milestone.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        due_date = cleaned_data.get('due_date')
        depends_on = cleaned_data.get('depends_on')

        if start_date and due_date and due_date < start_date:
            self.add_error('due_date', "Due date must be on or after the start date.")

        if self.instance and self.instance.pk and depends_on:
            if self.instance in depends_on:
                self.add_error('depends_on', "A milestone can't depend on itself.")
                return cleaned_data

            # Loop detection using DFS
            target_pk = self.instance.pk
            visited = set()

            def has_path(m_id):
                if m_id == target_pk:
                    return True
                if m_id in visited:
                    return False
                visited.add(m_id)
                dep_ids = Milestone.objects.filter(pk=m_id).values_list('depends_on', flat=True)
                for d_id in dep_ids:
                    if d_id and has_path(d_id):
                        return True
                return False

            for dep in depends_on:
                visited.clear()
                if has_path(dep.pk):
                    self.add_error('depends_on', f"That would create a loop: '{dep.title}' depends on this milestone.")
                    break

        return cleaned_data


class MilestoneProgressForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['status', 'progress']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'progress': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 100}),
        }
