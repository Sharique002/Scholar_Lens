from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from papers.models import ResearchPaper
from ai_engine.services import PaperSummarizer, ResearchGapDetector, ResearchQuestionAnswerer, PaperProcessor, AIServiceNotConfigured
from ai_engine.models import ChatMessage

@login_required
def paper_summary(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    summary = None
    error = None
    
    if request.method == 'POST':
        try:
            summarizer = PaperSummarizer()
            summary = summarizer.summarize(paper)
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=request.user,
                    activity_type='AI_ANALYSIS',
                    description=f"Generated structured AI summary for '{paper.title}'",
                    related_paper=paper
                )
            except Exception:
                pass
        except AIServiceNotConfigured:
            error = "AI service not configured. Please set the API key."
        except Exception as e:
            error = str(e)
            
    if not summary:
        from ai_engine.models import AIAnalysis
        analysis = AIAnalysis.objects.filter(paper=paper, analysis_type='SUMMARY').first()
        if analysis:
            summary = analysis.result

    return render(request, 'ai_engine/summary.html', {
        'paper': paper,
        'summary': summary,
        'error': error
    })

@login_required
def paper_gaps(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    gaps = []
    error = None
    
    if request.method == 'POST':
        try:
            detector = ResearchGapDetector()
            gaps = detector.detect_gaps(paper)
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=request.user,
                    activity_type='AI_ANALYSIS',
                    description=f"Detected research gaps for '{paper.title}'",
                    related_paper=paper
                )
            except Exception:
                pass
        except AIServiceNotConfigured:
            error = "AI service not configured. Please set the API key."
        except Exception as e:
            error = str(e)
            
    if not gaps:
        from ai_engine.models import ResearchGap
        gaps = ResearchGap.objects.filter(paper=paper)

    return render(request, 'ai_engine/gaps.html', {
        'paper': paper,
        'gaps': gaps,
        'error': error
    })

@login_required
def ask_paper(request, paper_id):
    paper = get_object_or_404(ResearchPaper, id=paper_id)
    error = None
    
    if request.method == 'POST':
        question = request.POST.get('question')
        if question:
            try:
                ai = AIService()
                if not ai.is_configured:
                    raise AIServiceNotConfigured("AI service not configured. Please set the API key.")
                answerer = ResearchQuestionAnswerer()
                answerer.answer_question(paper, question, request.user)
                try:
                    from dashboard.models import ResearchActivity
                    ResearchActivity.objects.create(
                        user=request.user,
                        activity_type='AI_ANALYSIS',
                        description=f"Queried paper '{paper.title}': {question[:50]}...",
                        related_paper=paper
                    )
                except Exception:
                    pass
                return redirect('ai_engine:ask_paper', paper_id=paper.id)
            except AIServiceNotConfigured:
                error = "AI service not configured. Please set the API key."
            except Exception as e:
                error = str(e)

    history = ChatMessage.objects.filter(paper=paper, user=request.user)
    return render(request, 'ai_engine/ask_paper.html', {
        'paper': paper,
        'history': history,
        'error': error
    })

@login_required
def process_paper_view(request, paper_id):
    if request.method == 'POST':
        paper = get_object_or_404(ResearchPaper, id=paper_id)
        processor = PaperProcessor()
        processor.process_paper(paper)
        return redirect('ai_engine:summary', paper_id=paper.id)
    return redirect('/')
