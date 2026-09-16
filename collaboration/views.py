from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.models import User
from .models import CollaborationRequest
from .forms import CollaborationRequestForm
from researchers.models import ResearcherProfile

@login_required
def collaboration_list(request):
    sent_requests = CollaborationRequest.objects.filter(sender=request.user)
    received_requests = CollaborationRequest.objects.filter(receiver=request.user)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        sent_requests = sent_requests.filter(status=status_filter)
        received_requests = received_requests.filter(status=status_filter)
        
    return render(request, 'collaboration/list.html', {
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'status_filter': status_filter,
    })

@login_required
def collaboration_send(request, receiver_id):
    receiver = get_object_or_404(User, pk=receiver_id)
    if receiver == request.user:
        messages.error(request, "You cannot send a collaboration request to yourself.")
        return redirect('researchers:list')
        
    # Prevent duplicate pending requests
    existing_pending = CollaborationRequest.objects.filter(
        sender=request.user, receiver=receiver, status='PENDING'
    ).first()
    if existing_pending:
        messages.warning(request, f"You already have a pending collaboration request to {receiver.username}.")
        return redirect('collaboration:list')
        
    if request.method == 'POST':
        form = CollaborationRequestForm(request.POST, user=request.user)
        if form.is_valid():
            collab_req = form.save(commit=False)
            collab_req.sender = request.user
            collab_req.receiver = receiver
            collab_req.save()
            
            # Log activity
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=request.user,
                    activity_type='COLLABORATION',
                    description=f"Sent collaboration request to {receiver.username}"
                )
            except Exception:
                pass

            messages.success(request, 'Collaboration request sent successfully.')
            return redirect('collaboration:list')
    else:
        form = CollaborationRequestForm(initial={'receiver': receiver}, user=request.user)
        
    return render(request, 'collaboration/send.html', {'form': form, 'receiver': receiver})

@login_required
def collaboration_respond(request, pk):
    collab_req = get_object_or_404(CollaborationRequest, pk=pk, receiver=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            collab_req.status = 'ACCEPTED'
            collab_req.save()
            messages.success(request, 'Collaboration request accepted.')
            
            # Log activity
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=request.user,
                    activity_type='COLLABORATION',
                    description=f"Accepted collaboration request from {collab_req.sender.username}"
                )
            except Exception:
                pass

            # Optional: auto-add to project if a project was attached
            if collab_req.project:
                from projects.models import ProjectMember
                ProjectMember.objects.get_or_create(project=collab_req.project, user=request.user, defaults={'role': 'RESEARCHER'})
        elif action == 'decline':
            collab_req.status = 'DECLINED'
            collab_req.save()
            messages.info(request, 'Collaboration request declined.')
    return redirect('collaboration:list')

@login_required
def collaboration_cancel(request, pk):
    collab_req = get_object_or_404(CollaborationRequest, pk=pk, sender=request.user)
    if request.method == 'POST' and collab_req.status == 'PENDING':
        collab_req.status = 'CANCELLED'
        collab_req.save()
        messages.success(request, 'Collaboration request cancelled.')
    return redirect('collaboration:list')

@login_required
def researcher_recommendations(request):
    user_profile, _ = ResearcherProfile.objects.get_or_create(user=request.user)
        
    user_interests = set(user_profile.interests.all())
    user_skills = set(user_profile.skills.all())
    
    if not user_interests and not user_skills:
        messages.warning(request, "Please add some interests or skills to your profile to get explainable recommendations.")
        return redirect('researchers:edit_profile')

    all_profiles = ResearcherProfile.objects.exclude(user=request.user).filter(
        is_available_for_collaboration=True
    ).select_related('user').prefetch_related('interests', 'skills', 'user__uploaded_papers')
    
    recommendations = []
    for profile in all_profiles:
        profile_interests = set(profile.interests.all())
        profile_skills = set(profile.skills.all())
        
        shared_interests = user_interests.intersection(profile_interests)
        shared_skills = user_skills.intersection(profile_skills)
        comp_skills = profile_skills - user_skills
        related_pubs = profile.user.uploaded_papers.count()
        
        # Calculate real explainable similarity
        total_union_interests = max(len(user_interests.union(profile_interests)), 1)
        interest_overlap_ratio = len(shared_interests) / total_union_interests
        skill_comp_ratio = min(1.0, len(comp_skills) / 3.0)
        pub_boost = min(10.0, related_pubs * 2.5)
        
        raw_score = (interest_overlap_ratio * 60.0) + (skill_comp_ratio * 30.0) + pub_boost
        if len(shared_interests) > 0 or len(comp_skills) > 0 or related_pubs > 0:
            final_score = round(min(98.0, max(25.0, raw_score)), 1)
            
            # Compute collaboration potential
            if final_score >= 70 and related_pubs >= 1:
                potential = 'High'
            elif final_score >= 45:
                potential = 'Medium'
            else:
                potential = 'Promising'

            recommendations.append({
                'profile': profile,
                'score': final_score,
                'shared_interests': list(shared_interests),
                'shared_interests_count': len(shared_interests),
                'complementary_skills': list(comp_skills),
                'complementary_skills_count': len(comp_skills),
                'related_publications_count': related_pubs,
                'collaboration_potential': potential,
            })
            
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    return render(request, 'collaboration/recommendations.html', {'recommendations': recommendations})
