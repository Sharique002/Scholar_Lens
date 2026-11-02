"""Duplicate detection, scoring, soft merging, and unmerging for Research Papers."""
from typing import Tuple, Optional
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.contrib.postgres.search import TrigramSimilarity
from rapidfuzz import fuzz

from .models import ResearchPaper, DuplicateCandidate
from .text import normalise_title
from dashboard import audit

DEDUP_TRIGRAM_MIN = getattr(settings, 'DEDUP_TRIGRAM_MIN', 0.35)
DEDUP_AUTO_MERGE = getattr(settings, 'DEDUP_AUTO_MERGE', 93.0)
DEDUP_REVIEW_MIN = getattr(settings, 'DEDUP_REVIEW_MIN', 80.0)

ANTONYMS = {
    ('supervised', 'unsupervised'),
    ('linear', 'nonlinear'),
    ('convex', 'nonconvex'),
    ('online', 'offline'),
    ('single', 'multi'),
    ('static', 'dynamic'),
    ('symmetric', 'asymmetric'),
    ('synchronous', 'asynchronous'),
    ('hardware', 'software'),
    ('lossless', 'lossy'),
    ('centralized', 'decentralized'),
    ('indoor', 'outdoor'),
    ('early', 'late'),
    ('monocular', 'stereo'),
    ('dense', 'sparse'),
    ('2d', '3d'),
    ('1', '2'),
    ('i', 'ii'),
    ('first', 'second')
}


def has_distinguishing_token(words_a, words_b) -> bool:
    """Check if token lists contain mutually exclusive qualifiers."""
    for t1, t2 in ANTONYMS:
        if (t1 in words_a and t2 in words_b) or (t2 in words_a and t1 in words_b):
            return True
    return False


def evaluate_pair(
    title_a: str,
    year_a: Optional[int],
    doi_a: Optional[str],
    title_b: str,
    year_b: Optional[int],
    doi_b: Optional[str]
) -> Tuple[bool, float, str]:
    """Pure evaluation of two paper signatures.

    Returns: (is_duplicate: bool, score: float, action: 'AUTO_MERGE' | 'REVIEW' | 'NEW')
    """
    # 1. Matching non-empty DOIs is always a duplicate
    clean_doi_a = (doi_a or '').strip().lower()
    clean_doi_b = (doi_b or '').strip().lower()
    if clean_doi_a and clean_doi_b and clean_doi_a == clean_doi_b:
        return True, 100.0, 'AUTO_MERGE'

    # 2. Incompatible years (> 1 year difference) -> NEW
    if year_a is not None and year_b is not None and abs(year_a - year_b) > 1:
        return False, 0.0, 'NEW'

    # 3. Normalised titles
    na = normalise_title(title_a)
    nb = normalise_title(title_b)
    if not na or not nb:
        return False, 0.0, 'NEW'

    words_a = na.split()
    words_b = nb.split()

    # 4. Short titles (< 4 words) NEVER auto-merge
    if len(words_a) < 4 or len(words_b) < 4:
        score = float(fuzz.ratio(na, nb))
        if score >= 90.0:
            return True, score, 'REVIEW'
        else:
            return False, score, 'NEW'

    # 5. Normal titles (>= 4 words)
    score = float(fuzz.token_set_ratio(na, nb))
    ratio_score = float(fuzz.ratio(na, nb))

    if has_distinguishing_token(words_a, words_b):
        score = min(score, 60.0)

    if score >= DEDUP_AUTO_MERGE and ratio_score >= 80.0:
        return True, score, 'AUTO_MERGE'
    elif score >= DEDUP_REVIEW_MIN:
        return True, score, 'REVIEW'
    else:
        return False, score, 'NEW'


def find_duplicate(
    title: str,
    year: Optional[int] = None,
    doi: Optional[str] = None,
    exclude_pk: Optional[int] = None
) -> Tuple[Optional[ResearchPaper], float, str]:
    """Find duplicate candidate for an incoming paper against the existing database.

    Returns: (matched_paper, score, action) where action is 'AUTO_MERGE', 'REVIEW', or 'NEW'.
    """
    clean_doi = (doi or '').strip()
    if clean_doi:
        doi_match = ResearchPaper.all_objects.filter(doi__iexact=clean_doi)
        if exclude_pk:
            doi_match = doi_match.exclude(pk=exclude_pk)
        target = doi_match.first()
        if target:
            return target.resolve(), 100.0, 'AUTO_MERGE'

    norm_title = normalise_title(title)
    if not norm_title:
        return None, 0.0, 'NEW'

    words = norm_title.split()

    candidates = (
        ResearchPaper.all_objects
        .annotate(similarity=TrigramSimilarity('normalised_title', norm_title))
        .filter(similarity__gte=DEDUP_TRIGRAM_MIN)
    )
    if exclude_pk:
        candidates = candidates.exclude(pk=exclude_pk)

    candidates = candidates.filter(merged_into__isnull=True)

    if year is not None:
        candidates = candidates.filter(Q(year__isnull=True) | Q(year__gte=year - 1, year__lte=year + 1))

    best_paper = None
    best_score = 0.0
    best_action = 'NEW'

    for cand in candidates:
        cand_norm = cand.normalised_title or normalise_title(cand.title)
        cand_words = cand_norm.split()

        # Year check
        if year is not None and cand.year is not None and abs(year - cand.year) > 1:
            continue

        if len(words) < 4 or len(cand_words) < 4:
            s = float(fuzz.ratio(norm_title, cand_norm))
            act = 'REVIEW' if s >= 90.0 else 'NEW'
        else:
            s = float(fuzz.token_set_ratio(norm_title, cand_norm))
            r = float(fuzz.ratio(norm_title, cand_norm))
            if has_distinguishing_token(words, cand_words):
                s = min(s, 60.0)

            if s >= DEDUP_AUTO_MERGE and r >= 80.0:
                act = 'AUTO_MERGE'
            elif s >= DEDUP_REVIEW_MIN:
                act = 'REVIEW'
            else:
                act = 'NEW'

        if act in ('AUTO_MERGE', 'REVIEW') and s > best_score:
            best_paper = cand.resolve()
            best_score = s
            best_action = act

    return best_paper, best_score, best_action


def merge(source_paper: ResearchPaper, target_paper: ResearchPaper, actor=None) -> None:
    """Soft merge source_paper into target_paper (canonical)."""
    if source_paper.pk == target_paper.pk:
        return
    canonical = target_paper.resolve()
    source_paper.merged_into = canonical
    source_paper.save(update_fields=['merged_into'])

    # Update candidate entries
    DuplicateCandidate.objects.filter(
        incoming_paper=source_paper,
        existing_paper=canonical
    ).update(
        status=DuplicateCandidate.Status.MERGED,
        reviewed_by=actor,
        reviewed_at=timezone.now()
    )

    # Audit log
    audit.record(
        actor=actor,
        action='paper.merged',
        target=source_paper,
        into_id=canonical.pk,
        into_title=canonical.title
    )


def unmerge(source_paper: ResearchPaper, actor=None) -> None:
    """Reversibly undo soft merge on source_paper. Idempotent."""
    if not source_paper.merged_into_id:
        return
    old_target = source_paper.merged_into
    source_paper.merged_into = None
    source_paper.save(update_fields=['merged_into'])

    # Audit log
    audit.record(
        actor=actor,
        action='paper.unmerged',
        target=source_paper,
        unmerged_from_id=old_target.pk if old_target else None
    )
