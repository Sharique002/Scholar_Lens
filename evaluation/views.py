from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from papers.models import ResearchPaper
from evaluation.models import EvaluationReport
from evaluation.services import ResearchEvaluator, SimilarityAnalyzer
from ai_engine.services import AIServiceNotConfigured


def is_evaluator(user):
    """Check if user has Faculty or Admin role, or is staff/superuser."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.is_faculty_or_admin)


@login_required
def evaluate_paper(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    report = EvaluationReport.objects.filter(paper=paper).first()
    error = None
    can_evaluate = is_evaluator(request.user)

    if request.method == 'POST':
        if not can_evaluate:
            messages.error(
                request,
                "Permission Denied: Only Faculty and Admin accounts have authorization to conduct academic novelty evaluations."
            )
            return redirect('papers:detail', pk=paper.pk)

        try:
            re_evaluate = request.POST.get('re_evaluate') == '1' or request.GET.get('re_evaluate') == '1'
            evaluator = ResearchEvaluator()
            report = evaluator.evaluate(paper, force_reevaluate=re_evaluate)
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=request.user,
                    activity_type='EVALUATION',
                    description=f"Evaluated paper '{paper.title}' v{report.paper_version} (Score: {report.overall_score:.1f}/100)",
                    related_paper=paper
                )
            except Exception:
                pass
            return redirect('evaluation:report', report_id=report.id)
        except AIServiceNotConfigured:
            error = "AI service not configured. Please set the API key."
        except Exception as e:
            error = str(e)

    return render(request, 'evaluation/evaluate.html', {
        'paper': paper,
        'report': report,
        'error': error,
        'can_evaluate': can_evaluate,
    })


@login_required
def evaluation_report(request, report_id):
    report = get_object_or_404(EvaluationReport, id=report_id)
    scores = report.scores.all()
    history = report.paper.evaluation_reports.all().order_by('-created_at')
    return render(request, 'evaluation/report.html', {
        'report': report,
        'paper': report.paper,
        'scores': scores,
        'history': history,
        'can_evaluate': is_evaluator(request.user),
    })

@login_required
def similarity_analysis(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    analyzer = SimilarityAnalyzer()
    error = None
    results = {}
    try:
        results = analyzer.analyze(paper)
    except AIServiceNotConfigured:
        error = "AI service not configured. Please set the API key."
    except Exception as e:
        error = str(e)
        
    return render(request, 'evaluation/similarity.html', {
        'paper': paper,
        'similar_papers': results.get('similar_papers', []),
        'error': error
    })
