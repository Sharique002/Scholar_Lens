"""
Custom middleware for Scholar Lens.
"""
import traceback
from django.shortcuts import render


class ExceptionCaptureMiddleware:
    """
    Middleware that captures all unhandled exceptions across the entire
    request-response lifecycle and renders errors/500.html with full diagnostics.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            error_trace = traceback.format_exc()
            print("=" * 60)
            print("[CRITICAL EXCEPTION CAPTURED BY MIDDLEWARE]")
            print(error_trace)
            print("=" * 60)
            return render(
                request,
                'errors/500.html',
                {'error_trace': error_trace},
                status=500
            )

    def process_exception(self, request, exception):
        error_trace = traceback.format_exc()
        print("=" * 60)
        print("[VIEW EXCEPTION CAPTURED BY MIDDLEWARE]")
        print(error_trace)
        print("=" * 60)
        return render(
            request,
            'errors/500.html',
            {'error_trace': error_trace},
            status=500
        )
