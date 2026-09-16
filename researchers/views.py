from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import ResearcherProfile, ResearchInterest, Skill
from .forms import ResearcherProfileForm, ResearchInterestForm, SkillForm

@login_required
def researcher_list(request):
    query = request.GET.get('q', '')
    availability = request.GET.get('availability', '')
    
    profiles = ResearcherProfile.objects.select_related('user').prefetch_related('interests', 'skills')
    
    if query:
        profiles = profiles.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(headline__icontains=query) |
            Q(expertise_summary__icontains=query)
        )
        
    if availability == 'true':
        profiles = profiles.filter(is_available_for_collaboration=True)
    elif availability == 'false':
        profiles = profiles.filter(is_available_for_collaboration=False)
        
    paginator = Paginator(profiles.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'researchers/list.html', {'page_obj': page_obj, 'query': query, 'availability': availability})

@login_required
def researcher_detail(request, pk):
    profile = get_object_or_404(ResearcherProfile.objects.select_related('user').prefetch_related('interests', 'skills'), pk=pk)
    
    papers = profile.user.uploaded_papers.all().order_by('-created_at')
    projects = profile.user.led_projects.all().order_by('-created_at')

    return render(request, 'researchers/detail.html', {
        'profile': profile,
        'papers': papers,
        'projects': projects
    })

@login_required
def researcher_profile_edit(request):
    profile, created = ResearcherProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ResearcherProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('researchers:detail', pk=profile.pk)
    else:
        form = ResearcherProfileForm(instance=profile)
        
    return render(request, 'researchers/edit_profile.html', {'form': form})

@login_required
def researcher_add_interest(request):
    profile, created = ResearcherProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ResearchInterestForm(request.POST)
        if form.is_valid():
            interest, created = ResearchInterest.objects.get_or_create(
                name=form.cleaned_data['name'],
                defaults={'category': form.cleaned_data['category']}
            )
            profile.interests.add(interest)
            messages.success(request, 'Interest added.')
            return redirect('researchers:edit_profile')
    return redirect('researchers:edit_profile')

@login_required
def researcher_remove_interest(request, pk):
    profile = get_object_or_404(ResearcherProfile, user=request.user)
    if request.method == 'POST':
        interest = get_object_or_404(ResearchInterest, pk=pk)
        profile.interests.remove(interest)
        messages.success(request, 'Interest removed.')
    return redirect('researchers:edit_profile')

@login_required
def researcher_add_skill(request):
    profile, created = ResearcherProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill, created = Skill.objects.get_or_create(
                name=form.cleaned_data['name'],
                defaults={'category': form.cleaned_data['category']}
            )
            profile.skills.add(skill)
            messages.success(request, 'Skill added.')
            return redirect('researchers:edit_profile')
    return redirect('researchers:edit_profile')
