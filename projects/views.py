from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import ResearchProject, ProjectMember
from .forms import ProjectForm, ProjectMemberForm

@login_required
def project_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    area = request.GET.get('area', '')

    projects = ResearchProject.objects.filter(is_public=True).select_related('leader')

    if query:
        projects = projects.filter(title__icontains=query)
    if status:
        projects = projects.filter(status=status)
    if area:
        projects = projects.filter(research_area=area)

    paginator = Paginator(projects.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'projects/list.html', {
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'area': area,
        'status_choices': ResearchProject.STATUS_CHOICES,
        'area_choices': ResearchProject.RESEARCH_AREA_CHOICES,
    })

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.leader = request.user
            project.save()
            ProjectMember.objects.create(project=project, user=request.user, role='LEADER')
            
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=request.user,
                    activity_type='PROJECT',
                    description=f"Created new research project '{project.title}'"
                )
            except Exception:
                pass

            messages.success(request, 'Project created successfully.')
            return redirect('projects:detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'projects/create.html', {'form': form})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(ResearchProject.objects.select_related('leader'), pk=pk)
    
    if not project.is_public and project.leader != request.user and not project.members.filter(user=request.user).exists():
        messages.error(request, "You don't have access to this project.")
        return redirect('projects:list')

    members = project.members.select_related('user').all()
    papers = project.leader.uploaded_papers.all() if hasattr(project.leader, 'uploaded_papers') else []
    member_form = ProjectMemberForm()

    return render(request, 'projects/detail.html', {
        'project': project,
        'members': members,
        'papers': papers,
        'member_form': member_form,
        'is_leader': project.leader == request.user
    })

@login_required
def project_delete(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, leader=request.user)
    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.success(request, f"Project '{title}' was successfully deleted.")
        return redirect('projects:list')
    return redirect('projects:detail', pk=pk)

@login_required
def project_edit(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, leader=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('projects:detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/edit.html', {'form': form, 'project': project})

@login_required
def project_add_member(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, leader=request.user)
    if request.method == 'POST':
        form = ProjectMemberForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            if project.members.filter(user=user).exists():
                messages.warning(request, 'User is already a member.')
            else:
                member = form.save(commit=False)
                member.project = project
                member.save()
                messages.success(request, 'Member added successfully.')
        else:
            messages.error(request, 'Error adding member.')
    return redirect('projects:detail', pk=pk)

@login_required
def project_leave(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk)
    if request.user == project.leader:
        messages.error(request, "Leader cannot leave the project.")
        return redirect('projects:detail', pk=pk)

    if request.method == 'POST':
        member = get_object_or_404(ProjectMember, project=project, user=request.user)
        member.delete()
        messages.success(request, 'You have left the project.')
        return redirect('projects:list')
    return redirect('projects:detail', pk=pk)
