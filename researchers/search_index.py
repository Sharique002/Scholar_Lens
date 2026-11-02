"""PostgreSQL Full-Text Search Vector indexing for Researcher Profiles."""
from typing import List, Optional
from django.db import models
from django.contrib.postgres.search import SearchVector
from .models import ResearcherProfile


def refresh_search_document(profile_ids: Optional[List[int]] = None) -> int:
    """Rebuild stored search_document for specified researcher profiles (or all if None).

    Weights:
    - Weight A: Interests and Skills
    - Weight B: Headline and Department (name and code)
    - Weight C: Expertise summary, User first_name and last_name
    - Weight D: Confirmed authored paper titles
    """
    qs = (
        ResearcherProfile.objects
        .select_related('user', 'department')
        .prefetch_related('interests', 'skills', 'authored_papers__paper')
    )
    if profile_ids:
        qs = qs.filter(pk__in=profile_ids)

    updated_count = 0
    for profile in qs:
        # Weight A: Interests and Skills
        interests = [i.name for i in profile.interests.all()]
        skills = [s.name for s in profile.skills.all()]
        text_a = " ".join(interests + skills).strip()

        # Weight B: Headline and Department
        dept_name = profile.department.name if profile.department else ""
        dept_code = profile.department.code if profile.department else ""
        text_b = f"{profile.headline} {dept_name} {dept_code}".strip()

        # Weight C: Summary, First and Last Name
        summary = profile.expertise_summary or ""
        first = profile.user.first_name or ""
        last = profile.user.last_name or ""
        username = profile.user.username or ""
        text_c = f"{summary} {first} {last} {username}".strip()

        # Weight D: Authored papers titles
        paper_titles = [
            ap.paper.title for ap in profile.authored_papers.all()
            if ap.match_status == 'CONFIRMED' and ap.paper
        ]
        text_d = " ".join(paper_titles).strip()

        # Construct SearchVector
        vectors = []
        if text_a:
            vectors.append(SearchVector(models.Value(text_a), weight='A'))
        if text_b:
            vectors.append(SearchVector(models.Value(text_b), weight='B'))
        if text_c:
            vectors.append(SearchVector(models.Value(text_c), weight='C'))
        if text_d:
            vectors.append(SearchVector(models.Value(text_d), weight='D'))

        if vectors:
            combined = vectors[0]
            for v in vectors[1:]:
                combined = combined + v
            ResearcherProfile.objects.filter(pk=profile.pk).update(search_document=combined)
        else:
            ResearcherProfile.objects.filter(pk=profile.pk).update(search_document=None)

        updated_count += 1

    return updated_count
