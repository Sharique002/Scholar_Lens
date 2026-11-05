"""ORCID and Crossref public metadata importers resilient to malformed records."""
import re
import json
import requests
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import ResearchPaper, PaperAuthor, ImportRun, DuplicateCandidate
from .dedup import find_duplicate
from dashboard.models import ResearchActivity
from dashboard import audit

USER_AGENT = 'ScholarLens/1.0 (mailto:scholar.lens@university.edu)'


def strip_html(text: str) -> str:
    if not text:
        return ''
    cleaned = re.sub(r'<[^>]+>', ' ', text)
    return ' '.join(cleaned.split())


def parse_year(val: Any) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, int) and 1800 <= val <= 2100:
        return val
    s = str(val).strip()
    match = re.search(r'\b(19\d\d|20\d\d)\b', s)
    if match:
        return int(match.group(0))
    match_leading = re.match(r'^\d{4}', s)
    if match_leading:
        y = int(match_leading.group(0))
        if 1800 <= y <= 2100:
            return y
    return None


def fetch_orcid_works(orcid_id: str) -> List[Dict[str, Any]]:
    """Fetch works from ORCID public API."""
    if getattr(settings, 'E2E', False):
        fixture_path = settings.BASE_DIR / 'tests' / 'fixtures' / 'orcid_sample.json'
        if fixture_path.exists():
            with open(fixture_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            items = []
            for g in data.get('group', []):
                summaries = g.get('work-summary', [])
                if summaries:
                    items.append(summaries[0])
            return items
    clean_orcid = orcid_id.strip()
    url = f"https://pub.orcid.org/v3.0/{clean_orcid}/works"
    headers = {
        'Accept': 'application/json',
        'User-Agent': USER_AGENT
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = []
    for g in data.get('group', []):
        summaries = g.get('work-summary', [])
        if summaries:
            items.append(summaries[0])
    return items


def fetch_crossref(query: str, rows: int = 20) -> List[Dict[str, Any]]:
    """Fetch works from Crossref REST API."""
    if getattr(settings, 'E2E', False):
        fixture_path = settings.BASE_DIR / 'tests' / 'fixtures' / 'crossref_sample.json'
        if fixture_path.exists():
            with open(fixture_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('message', {}).get('items', [])
    url = "https://api.crossref.org/works"
    params = {'query': query, 'rows': rows}
    headers = {'User-Agent': USER_AGENT}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get('message', {}).get('items', [])


def fetch_scopus(author_id: str, rows: int = 25) -> List[Dict[str, Any]]:
    """Fetch an author's works from the Elsevier Scopus Search API (licence-dependent; needs SCOPUS_API_KEY)."""
    api_key = getattr(settings, 'SCOPUS_API_KEY', '')
    if not api_key:
        raise ValueError("SCOPUS_API_KEY is not configured; Scopus import requires an Elsevier licence key.")
    resp = requests.get(
        "https://api.elsevier.com/content/search/scopus",
        params={'query': f"AU-ID({author_id.strip()})", 'count': rows},
        headers={'X-ELS-APIKey': api_key, 'Accept': 'application/json', 'User-Agent': USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    entries = resp.json().get('search-results', {}).get('entry', [])
    # Scopus returns [{"error": "Result set was empty"}] when there are no hits.
    return [e for e in entries if isinstance(e, dict) and 'error' not in e]


def to_record(raw_item: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
    """Sanitize and normalize an external record. Returns None if malformed/unusable."""
    if not isinstance(raw_item, dict):
        return None

    src = source.upper()

    if src == 'ORCID':
        title_obj = raw_item.get('title')
        if not isinstance(title_obj, dict):
            return None
        sub_title = title_obj.get('title')
        title_val = sub_title.get('value', '') if isinstance(sub_title, dict) else ''
        title = strip_html(title_val).strip()
        if not title:
            return None

        # Journal / Venue
        journal = raw_item.get('journal-title')
        venue = journal.get('value', '') if isinstance(journal, dict) else ''

        # Pub type
        raw_type = (raw_item.get('type') or '').lower()
        pub_type = 'CONFERENCE' if 'conference' in raw_type or 'proceeding' in raw_type else 'JOURNAL'

        # Year
        pub_date = raw_item.get('publication-date') or {}
        year_raw = pub_date.get('year', {}).get('value') if isinstance(pub_date.get('year'), dict) else None
        year = parse_year(year_raw)

        # DOI
        doi = None
        ext_ids = raw_item.get('external-ids', {}).get('external-id', [])
        if isinstance(ext_ids, list):
            for eid in ext_ids:
                if isinstance(eid, dict) and eid.get('external-id-type') == 'doi':
                    doi = (eid.get('external-id-value') or '').strip().lower() or None
                    break

        # Abstract
        abstract = raw_item.get('short-description') or ''
        if len(abstract) > 5000:
            abstract = abstract[:5000] + '... [truncated]'

        external_id = str(raw_item.get('put-code') or doi or '')
        external_url = f"https://doi.org/{doi}" if doi else f"https://orcid.org/{external_id}"

        return {
            'title': title[:512],
            'abstract': abstract or f"Publication on {title}",
            'year': year,
            'venue': (venue or '')[:255],
            'doi': doi,
            'pub_type': pub_type,
            'authors': [],
            'source': 'EXTERNAL',
            'external_id': external_id,
            'external_url': external_url,
        }

    elif src == 'CROSSREF':
        titles = raw_item.get('title')
        if not titles or not isinstance(titles, list) or not titles[0]:
            return None
        title = strip_html(str(titles[0])).strip()
        if not title:
            return None

        container = raw_item.get('container-title')
        venue = container[0] if (container and isinstance(container, list) and container[0]) else ''

        raw_type = (raw_item.get('type') or '').lower()
        pub_type = 'CONFERENCE' if 'proceedings' in raw_type else 'JOURNAL'

        year = None
        for k in ('published-print', 'published-online', 'issued', 'created'):
            val = raw_item.get(k)
            if isinstance(val, dict):
                dp = val.get('date-parts')
                if dp and isinstance(dp, list) and dp[0]:
                    year = parse_year(dp[0][0])
                    if year:
                        break
                dt = val.get('date-time')
                if dt:
                    year = parse_year(dt)
                    if year:
                        break

        doi = (raw_item.get('DOI') or '').strip().lower() or None

        abstract = raw_item.get('abstract') or ''
        abstract = strip_html(abstract).strip()
        if len(abstract) > 5000:
            abstract = abstract[:5000] + '... [truncated]'

        authors = []
        author_list = raw_item.get('author')
        if author_list and isinstance(author_list, list):
            for a in author_list:
                if not isinstance(a, dict):
                    continue
                given = a.get('given', '').strip()
                family = a.get('family', '').strip()
                name = f"{given} {family}".strip() if given else family
                if not name:
                    name = a.get('name', '').strip()
                if name:
                    orc = a.get('ORCID', '')
                    if orc and 'orcid.org/' in orc:
                        orc = orc.split('orcid.org/')[-1]
                    authors.append({'name': name, 'orcid': orc or None})

        external_id = doi or str(raw_item.get('prefix') or '')
        external_url = f"https://doi.org/{doi}" if doi else (raw_item.get('URL') or '')

        return {
            'title': title[:512],
            'abstract': abstract or f"Publication on {title}",
            'year': year,
            'venue': (venue or '')[:255],
            'doi': doi,
            'pub_type': pub_type,
            'authors': authors,
            'source': 'EXTERNAL',
            'external_id': external_id,
            'external_url': external_url,
        }

    elif src == 'SCOPUS':
        title = strip_html(str(raw_item.get('dc:title') or '')).strip()
        if not title:
            return None
        doi = (str(raw_item.get('prism:doi') or '')).strip().lower() or None
        subtype = str(raw_item.get('subtypeDescription') or '').lower()
        abstract = strip_html(str(raw_item.get('dc:description') or '')).strip()[:5000]
        creator = str(raw_item.get('dc:creator') or '').strip()
        eid = str(raw_item.get('eid') or '').strip()
        return {
            'title': title[:512],
            'abstract': abstract or f"Publication on {title}",
            'year': parse_year(raw_item.get('prism:coverDate')),
            'venue': str(raw_item.get('prism:publicationName') or '')[:255],
            'doi': doi,
            'pub_type': 'CONFERENCE' if 'conference' in subtype else 'JOURNAL',
            'authors': [{'name': creator, 'orcid': None}] if creator else [],
            'source': 'EXTERNAL',
            'external_id': eid or doi or '',
            'external_url': f"https://doi.org/{doi}" if doi else (
                f"https://www.scopus.com/record/display.uri?eid={eid}" if eid else ''
            ),
        }

    return None


def import_records(
    raw_items: List[Dict[str, Any]],
    source: str,
    import_run: Optional[ImportRun] = None,
    actor=None
) -> Dict[str, Any]:
    """Import a list of external records with error resilience and duplicate protection."""
    imported_count = 0
    duplicate_count = 0
    skipped_malformed = 0

    for raw in raw_items:
        rec = to_record(raw, source)
        if not rec:
            skipped_malformed += 1
            continue

        # Check duplicate
        dup, score, action = find_duplicate(
            title=rec['title'],
            year=rec['year'],
            doi=rec['doi']
        )

        if action == 'AUTO_MERGE' and dup:
            duplicate_count += 1
            continue

        try:
            with transaction.atomic():
                paper = ResearchPaper.objects.create(
                    uploader=None,
                    title=rec['title'],
                    abstract=rec['abstract'],
                    research_area=ResearchPaper.ResearchArea.OTHER,
                    venue=rec['venue'],
                    pub_type=rec['pub_type'],
                    doi=rec['doi'],
                    year=rec['year'],
                    source='EXTERNAL',
                    external_id=rec['external_id'],
                    external_url=rec['external_url'],
                    status=ResearchPaper.PaperStatus.TEXT_EXTRACTED,
                    is_external=True
                )

                for idx, author_info in enumerate(rec.get('authors', [])):
                    PaperAuthor.objects.create(
                        paper=paper,
                        name=author_info['name'],
                        order=idx + 1
                    )

                if action == 'REVIEW' and dup:
                    DuplicateCandidate.objects.create(
                        incoming_paper=paper,
                        existing_paper=dup,
                        similarity_score=score,
                        status=DuplicateCandidate.Status.PENDING
                    )

                imported_count += 1
        except Exception:
            skipped_malformed += 1

    if import_run:
        import_run.total_fetched = len(raw_items)
        import_run.imported_count = imported_count
        import_run.duplicate_count = duplicate_count
        import_run.skipped_malformed = skipped_malformed
        import_run.status = ImportRun.Status.SUCCESS
        import_run.save()

    # Log activity
    if actor:
        ResearchActivity.objects.create(
            user=actor,
            activity_type='IMPORT',
            description=f"Imported {imported_count} publications from {source} ({duplicate_count} duplicates, {skipped_malformed} skipped)."
        )

    if import_run:
        audit.record(
            actor=actor,
            action=f"import.{source.lower()}",
            target=import_run,
            imported=imported_count,
            duplicates=duplicate_count,
            skipped=skipped_malformed
        )

    return {
        'imported': imported_count,
        'duplicates': duplicate_count,
        'skipped': skipped_malformed
    }
