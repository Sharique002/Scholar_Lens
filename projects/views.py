from datetime import date, timedelta
from collections import defaultdict
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Q

from .models import ResearchProject, ProjectMember, Milestone
from .forms import ProjectForm, ProjectMemberForm, MilestoneForm, MilestoneProgressForm


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
            messages.error(request, 'Invalid form data.')
    return redirect('projects:detail', pk=pk)


@login_required
def project_leave(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk)
    if request.method == 'POST':
        if project.leader == request.user:
            messages.error(request, 'Project leaders cannot leave the project. Please transfer leadership first or delete the project.')
            return redirect('projects:detail', pk=pk)
        
        membership = ProjectMember.objects.filter(project=project, user=request.user).first()
        if membership:
            membership.delete()
            messages.success(request, 'You have left the project.')
            return redirect('projects:list')
    return redirect('projects:detail', pk=pk)


# --- Milestone Views (M7) ---

@login_required
def project_milestones(request, pk):
    project = get_object_or_404(ResearchProject.objects.select_related('leader'), pk=pk)

    if not project.is_public and project.leader != request.user and not project.members.filter(user=request.user).exists():
        messages.error(request, "You don't have access to this project.")
        return redirect('projects:list')

    milestones_qs = project.milestones.select_related('owner').prefetch_related('depends_on').order_by('due_date')
    milestones = list(milestones_qs)

    is_leader = (project.leader == request.user)
    today = date.today()

    timeline_items = []
    today_pct = None

    if milestones:
        all_starts = [m.start_date if m.start_date else (m.due_date - timedelta(days=7)) for m in milestones]
        all_ends = [m.due_date for m in milestones]

        proj_start = project.start_date or min(all_starts)
        proj_end = project.end_date or max(all_ends)

        if proj_start > min(all_starts):
            proj_start = min(all_starts)
        if proj_end < max(all_ends):
            proj_end = max(all_ends)

        total_days = (proj_end - proj_start).days
        if total_days <= 0:
            total_days = 1

        for m in milestones:
            m_start = m.start_date if m.start_date else (m.due_date - timedelta(days=7))
            m_end = m.due_date

            left_days = (m_start - proj_start).days
            dur_days = (m_end - m_start).days
            if dur_days <= 0:
                dur_days = 1

            left_pct = round(max(0.0, min(100.0, (left_days / total_days) * 100)), 1)
            width_pct = round(max(1.0, min(100.0 - left_pct, (dur_days / total_days) * 100)), 1)

            timeline_items.append({
                'milestone': m,
                'left': left_pct,
                'width': width_pct,
                'can_edit': is_leader,
                'can_update_progress': (is_leader or m.owner == request.user),
            })

        if proj_start <= today <= proj_end:
            today_pct = round(((today - proj_start).days / total_days) * 100, 1)

    return render(request, 'projects/milestones.html', {
        'project': project,
        'milestones': milestones,
        'timeline_items': timeline_items,
        'is_leader': is_leader,
        'today': today,
        'today_pct': today_pct,
    })


@login_required
def milestone_create(request, pk):
    project = get_object_or_404(ResearchProject, pk=pk, leader=request.user)
    if request.method == 'POST':
        form = MilestoneForm(request.POST, project=project)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.project = project
            milestone.save()
            form.save_m2m()
            messages.success(request, f"Milestone '{milestone.title}' added successfully.")
            return redirect('projects:milestones', pk=project.pk)
    else:
        form = MilestoneForm(project=project)

    return render(request, 'projects/milestone_form.html', {
        'form': form,
        'project': project,
        'action_title': 'Add Milestone',
    })


@login_required
def milestone_edit(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk, project__leader=request.user)
    project = milestone.project
    if request.method == 'POST':
        form = MilestoneForm(request.POST, instance=milestone, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Milestone '{milestone.title}' updated successfully.")
            return redirect('projects:milestones', pk=project.pk)
    else:
        form = MilestoneForm(instance=milestone, project=project)

    return render(request, 'projects/milestone_form.html', {
        'form': form,
        'project': project,
        'milestone': milestone,
        'action_title': f"Edit Milestone: {milestone.title}",
    })


@login_required
@require_POST
def milestone_delete(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk, project__leader=request.user)
    project_pk = milestone.project.pk
    title = milestone.title
    milestone.delete()
    messages.success(request, f"Milestone '{title}' deleted.")
    return redirect('projects:milestones', pk=project_pk)


@login_required
@require_POST
def milestone_progress(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk)
    if milestone.project.leader != request.user and milestone.owner != request.user:
        raise PermissionDenied("Only the milestone owner or project leader can update progress.")

    form = MilestoneProgressForm(request.POST, instance=milestone)
    if form.is_valid():
        form.save()
        messages.success(request, f"Progress updated for '{milestone.title}'.")
    else:
        messages.error(request, "Failed to update milestone progress.")

    return redirect('projects:milestones', pk=milestone.project.pk)


@login_required
def at_risk_board(request):
    if not request.user.is_staff:
        raise PermissionDenied("Only Research Office staff can view the at-risk project board.")

    at_risk_milestones = Milestone.objects.filter(
        risk__in=['AT_RISK', 'OVERDUE']
    ).select_related('project', 'project__leader', 'owner').order_by('project', 'due_date')

    today = date.today()
    projects_dict = defaultdict(list)
    for m in at_risk_milestones:
        days_late = (today - m.due_date).days if m.due_date < today else 0
        m.days_late = days_late
        projects_dict[m.project].append(m)

    grouped_projects = [{'project': p, 'milestones': m_list} for p, m_list in projects_dict.items()]

    return render(request, 'projects/at_risk.html', {
        'grouped_projects': grouped_projects,
        'total_at_risk': at_risk_milestones.filter(risk='AT_RISK').count(),
        'total_overdue': at_risk_milestones.filter(risk='OVERDUE').count(),
    })
