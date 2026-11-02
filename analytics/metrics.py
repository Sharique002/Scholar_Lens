from datetime import date
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.contrib.auth.models import User

from researchers.models import Department, ResearcherProfile
from papers.models import ResearchPaper, PaperAuthor
from funding.models import FundingApplication
from facilities.models import Booking
from projects.models import ResearchProject, ProjectMember


def is_dean(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.groups.filter(name__icontains='Dean').exists():
        return True
    profile = getattr(user, 'profile', None)
    if profile and getattr(profile, 'role', '') == 'DEAN':
        return True
    if 'dean' in user.username.lower():
        return True
    return False


def get_academic_year_range(year_str=None):
    """
    Returns (start_date, end_date, label).
    Academic years run July 1 to June 30.
    """
    if year_str and '-' in year_str:
        try:
            parts = year_str.split('-')
            start_yr = int(parts[0])
            end_yr = int(parts[1])
            return date(start_yr, 7, 1), date(end_yr, 6, 30), f"{start_yr}-{end_yr}"
        except Exception:
            pass
    elif year_str and year_str.isdigit():
        start_yr = int(year_str)
        return date(start_yr, 7, 1), date(start_yr + 1, 6, 30), f"{start_yr}-{start_yr + 1}"

    today = timezone.localdate()
    if today.month >= 7:
        start_yr = today.year
        end_yr = today.year + 1
    else:
        start_yr = today.year - 1
        end_yr = today.year

    return date(start_yr, 7, 1), date(end_yr, 6, 30), f"{start_yr}-{end_yr}"


def compute_academic_year_metrics(start_date, end_date, include_researchers=False):
    dept_metrics = []
    departments = Department.objects.all().order_by('name')

    total_pubs = 0
    total_funding_requested = 0.0
    total_funding_awarded = 0.0
    total_facility_hours = 0.0

    start_dt = timezone.make_aware(timezone.datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0))
    end_dt = timezone.make_aware(timezone.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))

    for dept in departments:
        # Researchers in department
        dept_researchers = ResearcherProfile.objects.filter(department=dept)
        dept_user_ids = list(dept_researchers.values_list('user_id', flat=True))

        # Papers
        dept_papers = ResearchPaper.objects.filter(
            authors__researcher__in=dept_researchers
        ).filter(
            Q(publication_date__range=(start_date, end_date)) |
            Q(year=start_date.year, publication_date__isnull=True)
        ).distinct()
        pub_count = dept_papers.count()
        total_pubs += pub_count

        # Funding Applications
        dept_fund_apps = FundingApplication.objects.filter(
            applicant_id__in=dept_user_ids,
            submitted_at__date__range=(start_date, end_date)
        )
        fund_total_count = dept_fund_apps.count()
        fund_awarded = dept_fund_apps.filter(status='AWARDED')
        fund_awarded_count = fund_awarded.count()

        req_sum = float(dept_fund_apps.aggregate(s=Sum('amount_requested'))['s'] or 0.0)
        awarded_sum = float(fund_awarded.aggregate(s=Sum('amount_awarded'))['s'] or 0.0)
        total_funding_requested += req_sum
        total_funding_awarded += awarded_sum

        success_rate = round((fund_awarded_count / fund_total_count * 100.0), 1) if fund_total_count > 0 else 0.0

        # Facility Bookings
        dept_bookings = Booking.objects.filter(
            user_id__in=dept_user_ids,
            status='APPROVED'
        )
        hours = 0.0
        for b in dept_bookings:
            if b.start and start_dt <= b.start <= end_dt:
                hours += b.hours
        hours = round(hours, 1)
        total_facility_hours += hours

        # Active Projects
        active_projects_count = ResearchProject.objects.filter(
            Q(leader_id__in=dept_user_ids) | Q(members__user_id__in=dept_user_ids)
        ).filter(status='ACTIVE').distinct().count()

        dept_metrics.append({
            'department': dept.name,
            'code': dept.code,
            'publications_count': pub_count,
            'funding_applications_count': fund_total_count,
            'funding_awarded_count': fund_awarded_count,
            'funding_requested_amount': req_sum,
            'funding_awarded_amount': awarded_sum,
            'funding_success_rate': success_rate,
            'facility_hours': hours,
            'active_projects_count': active_projects_count,
        })

    researcher_metrics = []
    if include_researchers:
        researchers = ResearcherProfile.objects.select_related('user', 'department').all().order_by('user__username')
        for r in researchers:
            r_papers = ResearchPaper.objects.filter(
                authors__researcher=r
            ).filter(
                Q(publication_date__range=(start_date, end_date)) |
                Q(year=start_date.year, publication_date__isnull=True)
            ).distinct().count()

            r_funds = FundingApplication.objects.filter(
                applicant=r.user,
                status='AWARDED',
                submitted_at__date__range=(start_date, end_date)
            )
            r_awarded_sum = float(r_funds.aggregate(s=Sum('amount_awarded'))['s'] or 0.0)

            r_projects = ResearchProject.objects.filter(
                Q(leader=r.user) | Q(members__user=r.user),
                status='ACTIVE'
            ).distinct().count()

            researcher_metrics.append({
                'username': r.user.username,
                'name': r.user.get_full_name() or r.user.username,
                'department': r.department.name if r.department else 'General',
                'publications_count': r_papers,
                'funding_awarded_amount': r_awarded_sum,
                'active_projects_count': r_projects,
            })

    summary = {
        'total_publications': total_pubs,
        'total_funding_requested': total_funding_requested,
        'total_funding_awarded': total_funding_awarded,
        'total_facility_hours': total_facility_hours,
    }

    return {
        'dept_metrics': dept_metrics,
        'researcher_metrics': researcher_metrics,
        'summary': summary,
    }
