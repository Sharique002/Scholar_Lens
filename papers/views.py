import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.contrib import messages
from django.db.models import Q

from .models import ResearchPaper
from .forms import PaperUploadForm, PaperEditForm, PaperAuthorFormSet


@login_required
def paper_list(request):
    """View to list and filter uploaded papers."""
    queryset = ResearchPaper.objects.select_related('uploader').all()
    
    # Filtering
    research_area = request.GET.get('research_area')
    if research_area:
        queryset = queryset.filter(research_area=research_area)
        
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(abstract__icontains=query) |
            Q(keywords__icontains=query)
        )
        
    # Pagination
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'research_areas': ResearchPaper.ResearchArea.choices,
        'current_area': research_area,
        'query': query,
    }
    return render(request, 'papers/list.html', context)


@login_required
def paper_upload(request):
    """View to upload a new research paper."""
    if request.method == 'POST':
        form = PaperUploadForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.uploader = request.user
            paper.status = ResearchPaper.PaperStatus.UPLOADED
            paper.save()
            
            has_formset = any('TOTAL_FORMS' in k for k in request.POST.keys())
            formset = PaperAuthorFormSet(request.POST, instance=paper) if has_formset else None
            if formset is None or formset.is_valid():
                if formset:
                    formset.save()

                # Trigger automated PDF text extraction & chunk indexing
                if paper.pdf_file:
                    try:
                        from ai_engine.services import PaperProcessor
                        PaperProcessor().process_paper(paper)
                    except Exception:
                        pass

                # Trigger Google Scholar similar paper discovery & comparative analysis
                try:
                    from evaluation.services import SimilarityAnalyzer
                    SimilarityAnalyzer().analyze(paper, fetch_scholar=True)
                except Exception as scholar_err:
                    import logging
                    logging.getLogger('scholar_lens').warning(
                        f"Google Scholar discovery/comparison non-fatal error: {scholar_err}"
                    )

                # Record activity in user feed
                try:
                    from dashboard.models import ResearchActivity
                    ResearchActivity.objects.create(
                        user=request.user,
                        activity_type='PAPER_UPLOAD',
                        description=f"Uploaded research paper '{paper.title}'",
                        related_paper=paper
                    )
                except Exception:
                    pass

                messages.success(request, "Paper uploaded and processed successfully.")
                return redirect('papers:detail', pk=paper.pk)
            else:
                messages.error(request, "Please correct the author errors below.")
        else:
            formset = PaperAuthorFormSet(request.POST)
    else:
        form = PaperUploadForm()
        formset = PaperAuthorFormSet()
        
    context = {
        'form': form,
        'formset': formset
    }
    return render(request, 'papers/upload.html', context)


@login_required
def paper_detail(request, pk):
    """View to see full details of a paper including AI analysis and evaluation."""
    paper = get_object_or_404(
        ResearchPaper.objects.prefetch_related('authors', 'chunks', 'research_gaps', 'evaluation_reports', 'ai_analyses'),
        pk=pk
    )
    
    latest_summary = paper.ai_analyses.filter(analysis_type='SUMMARY').first()
    research_gaps = paper.research_gaps.all()
    evaluation_report = paper.evaluation_reports.first()
    
    similar_papers = []
    try:
        from evaluation.services import SimilarityAnalyzer
        sim_res = SimilarityAnalyzer().analyze(paper)
        similar_papers = sim_res.get('similar_papers', [])
    except Exception:
        similar_papers = []
        
    from evaluation.views import is_evaluator

    context = {
        'paper': paper,
        'latest_summary': latest_summary,
        'summary_data': latest_summary.result if latest_summary else None,
        'research_gaps': research_gaps,
        'evaluation_report': evaluation_report,
        'similar_papers': similar_papers,
        'chunks_count': paper.chunks.count(),
        'can_evaluate': is_evaluator(request.user),
    }
    return render(request, 'papers/detail.html', context)


@login_required
def paper_edit(request, pk):
    """View to edit paper details (only accessible to uploader)."""
    paper = get_object_or_404(ResearchPaper, pk=pk)
    
    if paper.uploader != request.user:
        messages.error(request, "You do not have permission to edit this paper.")
        return redirect('papers:detail', pk=paper.pk)
        
    if request.method == 'POST':
        form = PaperEditForm(request.POST, instance=paper)
        has_formset = any('TOTAL_FORMS' in k for k in request.POST.keys())
        formset = PaperAuthorFormSet(request.POST, instance=paper) if has_formset else None
        
        if form.is_valid() and (formset is None or formset.is_valid()):
            form.save()
            if formset:
                formset.save()

            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=request.user,
                    activity_type='PAPER_EDIT',
                    description=f"Updated metadata for '{paper.title}'",
                    related_paper=paper
                )
            except Exception:
                pass

            messages.success(request, "Paper updated successfully.")
            return redirect('papers:detail', pk=paper.pk)
    else:
        form = PaperEditForm(instance=paper)
        formset = PaperAuthorFormSet(instance=paper)
        
    context = {
        'form': form,
        'formset': formset,
        'paper': paper
    }
    return render(request, 'papers/edit.html', context)


@login_required
def paper_delete(request, pk):
    """View to delete a paper (only accessible to uploader)."""
    paper = get_object_or_404(ResearchPaper, pk=pk)
    
    if paper.uploader != request.user:
        messages.error(request, "You do not have permission to delete this paper.")
        return redirect('papers:detail', pk=paper.pk)
        
    if request.method == 'POST':
        paper.delete()
        messages.success(request, "Paper deleted successfully.")
        return redirect('papers:list')
        
    context = {'paper': paper}
    return render(request, 'papers/confirm_delete.html', context)


@login_required
def paper_download(request, pk):
    """View to download the paper PDF."""
    paper = get_object_or_404(ResearchPaper, pk=pk)
    
    # We allow downloading if logged in, maybe add check if public later
    if not paper.pdf_file:
        raise Http404("PDF file not found.")
        
    file_path = paper.pdf_file.path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
    else:
        raise Http404("PDF file not found on server.")
