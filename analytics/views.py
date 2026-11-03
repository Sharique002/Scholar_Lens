import csv
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from .metrics import is_dean, get_academic_year_range, compute_academic_year_metrics


@login_required
def research_report(request):
    if not (request.user.is_staff or is_dean(request.user)):
        raise PermissionDenied("Only Research Office staff and the Dean of Research can access academic reports.")

    year_param = request.GET.get('year', '').strip()
    export = request.GET.get('export', '').strip().lower()
    section = request.GET.get('section', '').strip().lower()

    start_date, end_date, year_label = get_academic_year_range(year_param)
    user_is_dean = is_dean(request.user)

    data = compute_academic_year_metrics(
        start_date=start_date,
        end_date=end_date,
        include_researchers=user_is_dean
    )

    if export == 'csv' or request.GET.get('format') == 'csv' or section == 'all':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="scholar_lens_research_report_{year_label}.csv"'
        writer = csv.writer(response)

        writer.writerow(['Departmental Productivity Report', f'Academic Year {year_label}'])
        writer.writerow([
            'Department',
            'Publications',
            'Funding Requested',
            'Funding Awarded',
            'Success Rate (%)',
            'Facility Hours',
            'Active Projects'
        ])
        for d in data['dept_metrics']:
            writer.writerow([
                d['department'],
                d['publications_count'],
                d['funding_requested_amount'],
                d['funding_awarded_amount'],
                d['funding_success_rate'],
                d['facility_hours'],
                d['active_projects_count']
            ])

        if user_is_dean and data['researcher_metrics']:
            writer.writerow([])
            writer.writerow(['Individual Researcher Productivity (Dean Confidential)', f'Academic Year {year_label}'])
            writer.writerow(['Researcher', 'Department', 'Publications', 'Funding Awarded', 'Active Projects'])
            for r in data['researcher_metrics']:
                writer.writerow([
                    r['username'],
                    r['department'],
                    r['publications_count'],
                    r['funding_awarded_amount'],
                    r['active_projects_count']
                ])

        return response

    return render(request, 'analytics/report.html', {
        'year_label': year_label,
        'start_date': start_date,
        'end_date': end_date,
        'dept_metrics': data['dept_metrics'],
        'researcher_metrics': data['researcher_metrics'],
        'summary': data['summary'],
        'is_dean': user_is_dean,
    })
