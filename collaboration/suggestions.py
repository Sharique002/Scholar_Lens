from django.db.models import Q
from researchers.models import ResearcherProfile
from papers.models import PaperAuthor
from projects.models import ResearchProject, ProjectMember
from dashboard.models import ResearchActivity
from .models import CollaborationSuggestion


def score_pair(r1: ResearcherProfile, r2: ResearcherProfile):
    """
    Computes collaboration score between r1 and r2 based on:
    - Expertise adjacency (shared interests, shared parent taxonomy categories, complementary skills, cross-department bonus)
    - Co-authorship gap (awards +30 if researchers have never co-authored a paper or shared a project)
    """
    if r1.pk == r2.pk:
        return 0.0, 0.0, 0.0, {}

    interests1 = set(r1.interests.all())
    interests2 = set(r2.interests.all())
    shared_interests = interests1.intersection(interests2)

    parents1 = set(i.parent for i in interests1 if i.parent)
    parents2 = set(i.parent for i in interests2 if i.parent)
    shared_parents = parents1.intersection(parents2)

    skills1 = set(r1.skills.all())
    skills2 = set(r2.skills.all())
    comp_skills = skills2 - skills1

    is_cross_dept = bool(
        r1.department_id and r2.department_id and r1.department_id != r2.department_id
    )

    # Adjacency components
    shared_int_score = min(40.0, len(shared_interests) * 20.0)
    shared_parent_score = min(15.0, len(shared_parents) * 10.0)
    comp_skill_score = min(20.0, len(comp_skills) * 10.0)
    dept_score = 15.0 if is_cross_dept else 0.0

    adjacency_score = min(70.0, shared_int_score + shared_parent_score + comp_skill_score + dept_score)

    # Co-authorship & co-project detection
    r1_papers = set(PaperAuthor.objects.filter(researcher=r1).values_list('paper_id', flat=True))
    r2_papers = set(PaperAuthor.objects.filter(researcher=r2).values_list('paper_id', flat=True))
    has_coauthored = bool(r1_papers.intersection(r2_papers))

    r1_projects = set(ProjectMember.objects.filter(user=r1.user).values_list('project_id', flat=True))
    r1_projects.update(ResearchProject.objects.filter(leader=r1.user).values_list('id', flat=True))
    r2_projects = set(ProjectMember.objects.filter(user=r2.user).values_list('project_id', flat=True))
    r2_projects.update(ResearchProject.objects.filter(leader=r2.user).values_list('id', flat=True))
    has_coproject = bool(r1_projects.intersection(r2_projects))

    # Gap bonus
    if not has_coauthored and not has_coproject:
        gap_score = 30.0
    else:
        gap_score = 0.0

    total_score = round(min(100.0, max(0.0, adjacency_score + gap_score)), 1)

    explanation = {
        'shared_interests': [i.name for i in shared_interests],
        'shared_categories': [p.name for p in shared_parents if p],
        'complementary_skills': [s.name for s in comp_skills],
        'is_cross_department': is_cross_dept,
        'has_coauthored': has_coauthored,
        'has_coproject': has_coproject,
    }

    return total_score, round(adjacency_score, 1), round(gap_score, 1), explanation


def compute_suggestions(target_researcher=None, top_k=10):
    """
    Computes collaboration suggestions for target_researcher or all available researchers.
    """
    if target_researcher:
        candidates = ResearcherProfile.objects.exclude(
            pk=target_researcher.pk
        ).filter(
            is_available_for_collaboration=True
        ).select_related('user', 'department').prefetch_related('interests__parent', 'skills')

        scored = []
        for cand in candidates:
            score, adj, gap, expl = score_pair(target_researcher, cand)
            if score > 0:
                scored.append((cand, score, adj, gap, expl))

        scored.sort(key=lambda x: x[1], reverse=True)

        for cand, score, adj, gap, expl in scored[:top_k]:
            _, created = CollaborationSuggestion.objects.update_or_create(
                researcher=target_researcher,
                suggested=cand,
                defaults={
                    'score': score,
                    'adjacency_score': adj,
                    'gap_score': gap,
                    'explanation': expl,
                }
            )
            if created:  # notify once per new pairing, not on every recompute
                ResearchActivity.objects.create(
                    user=target_researcher.user,
                    activity_type='SUGGESTION',
                    description=f"New collaboration suggestion: {cand.user.get_full_name() or cand.user.username}",
                )
    else:
        all_researchers = ResearcherProfile.objects.filter(
            is_available_for_collaboration=True
        ).select_related('user', 'department').prefetch_related('interests__parent', 'skills')

        for r in all_researchers:
            compute_suggestions(target_researcher=r, top_k=top_k)
