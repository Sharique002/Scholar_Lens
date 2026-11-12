from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegistrationForm, LoginForm, UserProfileForm, UserUpdateForm
from .models import UserProfile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            institution = form.cleaned_data.get('institution')
            
            # Profile is automatically created via signals, so we just update it
            profile = user.profile
            profile.role = role
            profile.institution = institution
            profile.save()
            
            # Also ensure ResearcherProfile is created for collaboration & directory
            try:
                from researchers.models import ResearcherProfile
                ResearcherProfile.objects.get_or_create(user=user)
            except Exception:
                pass

            login(request, user)
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=user,
                    activity_type='LOGIN',
                    description=f"User {user.username} registered and logged in"
                )
            except Exception:
                pass
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('dashboard:home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            try:
                from dashboard.models import ResearchActivity
                ResearchActivity.objects.create(
                    user=user,
                    activity_type='LOGIN',
                    description=f"User {user.username} logged into Scholar Lens"
                )
            except Exception:
                pass
            messages.success(request, f"Welcome back, {user.username}!")
            # Get and validate 'next' parameter to prevent open redirect vulnerabilities
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect('dashboard:home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('/')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = UserProfileForm(instance=request.user.profile)
        
    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Updating the password logs out all other sessions for the user
            # except the current one.
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'accounts/change_password.html', {'form': form})



# ==========================================
# Google OAuth2 / SSO Authentication Views
# ==========================================
from django.conf import settings
from .google_auth import (
    is_google_auth_configured,
    get_google_auth_url,
    get_redirect_uri,
    exchange_code_for_user_info,
    get_or_create_google_user,
)


def google_login_view(request):
    """Initiate Google OAuth2 authentication flow."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    next_url = request.GET.get('next') or request.POST.get('next')
    if not is_google_auth_configured():
        if settings.DEBUG or request.GET.get('mock') == '1':
            return redirect(f"{reverse('accounts:google_mock')}?next={next_url or ''}")
        messages.error(
            request,
            "Google OAuth is not configured yet. Please configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
        )
        return redirect('accounts:login')

    auth_url, _ = get_google_auth_url(request, next_url=next_url)
    return redirect(auth_url)


def google_callback_view(request):
    """Handle Google OAuth2 callback code exchange and login."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    error = request.GET.get('error')
    if error:
        messages.warning(request, f"Google authentication was cancelled or failed ({error}).")
        return redirect('accounts:login')

    state = request.GET.get('state')
    expected_state = request.session.pop('google_oauth_state', None)
    raw_next = request.session.pop('google_oauth_next', None) or 'dashboard:home'
    if raw_next and raw_next != 'dashboard:home':
        if url_has_allowed_host_and_scheme(url=raw_next, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            next_url = raw_next
        else:
            next_url = 'dashboard:home'
    else:
        next_url = 'dashboard:home'

    if not state or state != expected_state:
        messages.error(request, "Authentication state mismatch. For security, please try signing in again.")
        return redirect('accounts:login')

    code = request.GET.get('code')
    if not code:
        messages.error(request, "Missing Google authorization code.")
        return redirect('accounts:login')

    try:
        stored_redirect_uri = request.session.pop('google_oauth_redirect_uri', None)
        redirect_uri = stored_redirect_uri or get_redirect_uri(request)
        user_info = exchange_code_for_user_info(code, redirect_uri)
        user, created = get_or_create_google_user(user_info)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        try:
            from dashboard.models import ResearchActivity
            action = "registered and signed in" if created else "signed in"
            ResearchActivity.objects.create(
                user=user,
                activity_type='LOGIN',
                description=f"User {user.username} {action} via Google OAuth2 Single Sign-On"
            )
        except Exception:
            pass

        greeting = "Welcome" if created else "Welcome back"
        messages.success(request, f"{greeting}, {user.first_name or user.username}! Successfully authenticated with Google ({user.email}).")
        return redirect(next_url)

    except Exception as e:
        messages.error(request, f"Failed to complete Google authentication: {str(e)}")
        return redirect('accounts:login')


def google_mock_view(request):
    """Mock Google sign-in for development, testing, and CI environments."""
    if not settings.DEBUG:
        messages.error(request, "Mock authentication is disabled in production.")
        return redirect('accounts:login')

    if request.user.is_authenticated:
        return redirect('dashboard:home')

    raw_next = request.GET.get('next') or request.POST.get('next') or 'dashboard:home'
    if raw_next and raw_next != 'dashboard:home':
        if url_has_allowed_host_and_scheme(url=raw_next, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            next_url = raw_next
        else:
            next_url = 'dashboard:home'
    else:
        next_url = 'dashboard:home'

    if request.method == 'POST':
        email = request.POST.get('email', 'shariquehussain03@gmail.com').strip()
        name = request.POST.get('name', 'Sharique Hussain').strip()
        role = request.POST.get('role', 'FACULTY')

        mock_payload = {
            'email': email,
            'name': name,
            'given_name': name.split()[0] if name else 'Sharique',
            'family_name': name.split()[-1] if len(name.split()) > 1 else '',
            'picture': 'https://lh3.googleusercontent.com/a/default-user',
            'sub': 'google_mock_123456789',
        }
        user, created = get_or_create_google_user(mock_payload)
        if hasattr(user, 'profile'):
            user.profile.role = role
            user.profile.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        try:
            from dashboard.models import ResearchActivity
            ResearchActivity.objects.create(
                user=user,
                activity_type='LOGIN',
                description=f"User {user.username} signed in via Mock Google SSO"
            )
        except Exception:
            pass

        messages.success(request, f"Successfully signed in with Google Account ({email})!")
        return redirect(next_url)

    return render(request, 'accounts/google_mock.html', {'next': next_url})