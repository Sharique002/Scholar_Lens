"""Author disambiguation, name matching, and review queue logic."""
import re
import unicodedata
from typing import List, Tuple, Optional
from django.utils import timezone
from rapidfuzz import fuzz

from .models import ResearchPaper, PaperAuthor
from researchers.models import ResearcherProfile
from dashboard import audit


def strip_titles(name: str) -> str:
    cleaned = re.sub(r'^(dr\.|prof\.|mr\.|ms\.|mrs\.|er\.)\s+', '', name, flags=re.IGNORECASE)
    return cleaned.strip()


def normalise_name(name: str) -> str:
    """Normalize author name: unaccent, handle 'Last, First', strip punctuation, lowercase."""
    if not name:
        return ''
    cleaned = strip_titles(name)
    if ',' in cleaned:
        parts = cleaned.split(',', 1)
        cleaned = f"{parts[1].strip()} {parts[0].strip()}"

    # NFKD and strip combining accents
    text = unicodedata.normalize('NFKD', cleaned)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Strip punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.lower().split())


def name_score(author_name: str, researcher: ResearcherProfile) -> float:
    """Compute matching confidence (0-100) between an author string and a ResearcherProfile."""
    norm_author = normalise_name(author_name)
    if not norm_author:
        return 0.0

    first = normalise_name(researcher.user.first_name)
    last = normalise_name(researcher.user.last_name)
    full = f"{first} {last}".strip()

    if not full:
        return 0.0

    # Exact full name match
    if norm_author == full:
        return 100.0

    # Token sort ratio on full name
    sort_ratio = float(fuzz.token_sort_ratio(norm_author, full))
    if sort_ratio >= 95.0:
        return sort_ratio

    # Check initial variant (e.g. "R. Kumar" -> "r kumar")
    author_tokens = norm_author.split()
    if len(author_tokens) == 2 and first and last:
        # First initial + last name
        if author_tokens[0] == first[0] and author_tokens[1] == last:
            # Initial only match: ambiguous, returns 85.0 (flag for review)
            return 85.0
        # Last name + first initial
        if author_tokens[1] == first[0] and author_tokens[0] == last:
            return 85.0

    if sort_ratio >= 80.0:
        return sort_ratio

    return 0.0


def match_authors(paper: Optional[ResearchPaper] = None) -> List[PaperAuthor]:
    """Run disambiguation against ResearcherProfiles for unmatched PaperAuthor records."""
    qs = PaperAuthor.objects.filter(match_status='UNMATCHED')
    if paper:
        qs = qs.filter(paper=paper)

    matched = []
    all_profiles = list(ResearcherProfile.objects.select_related('user', 'department').all())

    for author in qs:
        # 1. Exact ORCID match (100.0)
        if author.orcid:
            cand = next((p for p in all_profiles if p.orcid_id and p.orcid_id.strip().lower() == author.orcid.strip().lower()), None)
            if cand:
                author.researcher = cand
                author.match_status = PaperAuthor.MatchStatus.CONFIRMED
                author.match_score = 100.0
                author.matched_at = timezone.now()
                author.save()
                matched.append(author)
                continue

        # 2. Name scoring against profiles
        scored = []
        for p in all_profiles:
            s = name_score(author.name, p)
            if s >= 80.0:
                scored.append((p, s))

        if not scored:
            continue

        scored.sort(key=lambda x: x[1], reverse=True)
        best_p, best_s = scored[0]

        # Ambiguity check: if multiple candidates have close scores
        if len(scored) > 1 and (best_s < 95.0 or (best_s - scored[1][1]) < 5.0) and scored[1][1] >= 80.0:
            author.researcher = best_p
            author.match_status = PaperAuthor.MatchStatus.PENDING_REVIEW
            author.match_score = best_s
            author.save()
            matched.append(author)
            continue

        if best_s >= 92.0:
            author.researcher = best_p
            author.match_status = PaperAuthor.MatchStatus.CONFIRMED
            author.match_score = best_s
            author.matched_at = timezone.now()
            author.save()
            matched.append(author)
        elif best_s >= 80.0:
            author.researcher = best_p
            author.match_status = PaperAuthor.MatchStatus.PENDING_REVIEW
            author.match_score = best_s
            author.save()
            matched.append(author)

    return matched
