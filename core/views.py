import json
import uuid
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.db.models import F, Q
from django.utils import timezone
from .models import Poll, Option, VoteLog
from .forms import RegisterForm, LoginForm, PollCreateForm

COOKIE_VOTER_TOKEN_NAME = 'krarsizim_voter_token'
COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year


def get_or_create_voter_token(request):
    """
    Retrieves or generates a permanent device/browser voter token.
    Prevents duplicate votes even after logging out or session clearing.
    """
    token = request.COOKIES.get(COOKIE_VOTER_TOKEN_NAME)
    is_new = False
    if not token or len(token) < 16:
        token = uuid.uuid4().hex
        is_new = True
    return token, is_new


def migrate_anonymous_votes(request, user):
    """
    When an anonymous visitor registers or logs in, link their past anonymous votes
    from the current session to their newly authenticated user account.
    """
    old_session_key = request.session.session_key
    if old_session_key:
        VoteLog.objects.filter(session_key=old_session_key, user__isnull=True).update(user=user)


def index_view(request):
    """
    Main home page view.
    Lists all polls in chronological order (newest first).
    Prefetches options and author, and calculates whether current user or guest has already voted.
    Uses user-specific lookup for authenticated users, and device/session lookup for guests.
    """
    polls = Poll.objects.prefetch_related('options', 'author').all()
    poll_form = PollCreateForm() if request.user.is_authenticated else None
    voter_token, is_new_cookie = get_or_create_voter_token(request)
    session_key = request.session.session_key

    # Lookup existing votes
    if request.user.is_authenticated:
        # Authenticated users are tracked strictly by their user account
        logs = VoteLog.objects.filter(user=request.user).values_list('poll_id', 'option_id')
    else:
        # Anonymous visitors are tracked by permanent device token cookie and session key
        q = Q()
        if voter_token:
            q |= Q(voter_token=voter_token)
        if session_key:
            q |= Q(session_key=session_key)
        logs = VoteLog.objects.filter(q).values_list('poll_id', 'option_id') if q else []

    user_votes = dict(logs)

    # Prepare poll items with vote state and percentages
    poll_data = []
    for poll in polls:
        voted_option_id = user_votes.get(poll.id)
        has_voted = (voted_option_id is not None)
        is_closed = poll.is_closed
        show_results = has_voted or is_closed
        total = poll.total_votes

        options_list = []
        for opt in poll.options.all():
            options_list.append({
                'id': opt.id,
                'text': opt.text,
                'vote_count': opt.vote_count,
                'percentage': opt.get_percentage(total),
                'is_selected': (opt.id == voted_option_id),
            })

        poll_data.append({
            'poll': poll,
            'has_voted': has_voted,
            'is_closed': is_closed,
            'show_results': show_results,
            'status_label': poll.status_label,
            'voted_option_id': voted_option_id,
            'total_votes': total,
            'options': options_list,
        })

    context = {
        'page_title': 'Ana Sayfa - Kararsız kaldığın her şey burada!',
        'poll_data': poll_data,
        'poll_form': poll_form,
    }
    response = render(request, 'core/index.html', context)
    if is_new_cookie:
        response.set_cookie(COOKIE_VOTER_TOKEN_NAME, voter_token, max_age=COOKIE_MAX_AGE, samesite='Lax')
    return response


def register_view(request):
    """
    User registration view.
    Ensures username, email, and password are provided.
    Migrates previous anonymous votes to user account upon registration.
    """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                migrate_anonymous_votes(request, user)
                login(request, user)
                messages.success(request, f'Hoş geldin @{user.username}! Hesabın başarıyla oluşturuldu.')
                return redirect('index')
            except IntegrityError:
                # Concurrent submission / race condition handling (e.g. mobile rapid double-click)
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    migrate_anonymous_votes(request, user)
                    login(request, user)
                    messages.success(request, f'Hoş geldin @{user.username}! Hesabın başarıyla oluşturuldu.')
                    return redirect('index')
                else:
                    form.add_error('username', 'Bu kullanıcı adı veya e-posta adresi zaten kullanımda.')
                    messages.error(request, 'Bu kullanıcı adı veya e-posta adresi zaten kullanımda.')
        else:
            messages.error(request, 'Lütfen formdaki hataları düzeltin.')
    else:
        form = RegisterForm()

    return render(request, 'core/register.html', {'form': form, 'page_title': 'Kayıt Ol'})


def login_view(request):
    """
    User login view.
    Migrates previous anonymous votes to user account upon login.
    """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            migrate_anonymous_votes(request, user)
            login(request, user)
            messages.success(request, f'Tekrar hoş geldin @{user.username}!')
            next_url = request.GET.get('next') or 'index'
            return redirect(next_url)
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form, 'page_title': 'Giriş Yap'})


def logout_view(request):
    """
    User logout view.
    """
    logout(request)
    messages.info(request, 'Başarıyla çıkış yaptın. Tekrar görüşmek üzere!')
    return redirect('index')


@login_required
def poll_create_view(request):
    """
    Poll creation view.
    Accessible only by logged-in users (@login_required).
    Validates question and options (strictly 2 to 5 options).
    Calculates expires_at according to selected duration.
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = PollCreateForm(request.POST)
        raw_options = request.POST.getlist('options') or request.POST.getlist('options[]')

        # Clean whitespace and filter out empty options
        options = [opt.strip() for opt in raw_options if opt and opt.strip()]

        errors = []
        if not form.is_valid():
            for field, field_errors in form.errors.items():
                for err in field_errors:
                    errors.append(err)

        # Validate 2 to 5 options constraint
        if len(options) < 2:
            errors.append('Bir anket en az 2 seçenekten oluşmalıdır.')
        elif len(options) > 5:
            errors.append('Bir anket en fazla 5 seçenekten oluşabilir.')

        for opt in options:
            if len(opt) > 120:
                errors.append(f'"{opt[:20]}..." seçeneği en fazla 120 karakter olabilir.')
                break

        # Check duplicate options
        lowered_opts = [o.lower() for o in options]
        if len(lowered_opts) != len(set(lowered_opts)):
            errors.append('Seçenekler birbirinden farklı olmalıdır.')

        if not errors:
            poll = form.save(commit=False)
            poll.author = request.user

            # Calculate expiration time based on duration choice
            duration = request.POST.get('duration') or '24h'
            now = timezone.now()
            if duration == '1h':
                poll.expires_at = now + timedelta(hours=1)
            elif duration == '6h':
                poll.expires_at = now + timedelta(hours=6)
            elif duration == '12h':
                poll.expires_at = now + timedelta(hours=12)
            elif duration == '24h':
                poll.expires_at = now + timedelta(hours=24)
            elif duration == '3d':
                poll.expires_at = now + timedelta(days=3)
            elif duration == '7d':
                poll.expires_at = now + timedelta(days=7)
            else:
                poll.expires_at = None  # 'never'

            poll.save()
            for opt_text in options:
                Option.objects.create(poll=poll, text=opt_text)

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Anketin başarıyla yayınlandı!',
                    'poll_id': poll.id,
                    'redirect_url': '/'
                })

            messages.success(request, '🎉 Anketin başarıyla yayınlandı!')
            return redirect('index')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)

            for err in errors:
                messages.error(request, err)
    else:
        form = PollCreateForm()
        options = ['', '']

    return render(request, 'core/poll_create.html', {
        'form': form,
        'page_title': 'Yeni Anket Oluştur',
        'initial_options': options
    })


@require_POST
def poll_vote_api(request, poll_id):
    """
    JSON voting endpoint for both members and anonymous visitors.
    Prevents duplicate votes across sessions, logins, and logouts using:
    - request.user (for authenticated members)
    - voter_token (permanent browser cookie)
    - session_key (Django session)
    """
    poll = get_object_or_404(Poll, id=poll_id)
    voter_token, is_new_cookie = get_or_create_voter_token(request)

    # Check if poll is closed
    if poll.is_closed:
        return JsonResponse({
            'success': False,
            'error': 'Bu anket oylamaya kapatılmıştır. Yeni oy kullanılamaz.'
        }, status=400)

    # Parse option_id from JSON body or form-data
    option_id = None
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            option_id = body.get('option_id')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Geçersiz veri formatı.'}, status=400)
    else:
        option_id = request.POST.get('option_id')

    if not option_id:
        return JsonResponse({'success': False, 'error': 'Lütfen oy vermek istediğiniz seçeneği belirtin.'}, status=400)

    try:
        option = poll.options.get(id=int(option_id))
    except (Option.DoesNotExist, ValueError):
        return JsonResponse({'success': False, 'error': 'Geçersiz seçenek seçildi.'}, status=400)

    # Identify voter
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    # Check for duplicate vote using user account for members, or token/session for guests
    if user:
        already_voted = VoteLog.objects.filter(poll=poll, user=user).exists()
    else:
        q = Q(voter_token=voter_token)
        if session_key:
            q |= Q(session_key=session_key)
        already_voted = VoteLog.objects.filter(poll=poll).filter(q).exists()

    if already_voted:
        return JsonResponse({
            'success': False,
            'error': 'Bu ankete zaten oy kullandınız.'
        }, status=400)

    # Atomically increment vote count and log the vote with user, session_key, and voter_token!
    with transaction.atomic():
        Option.objects.filter(id=option.id).update(vote_count=F('vote_count') + 1)
        VoteLog.objects.create(
            poll=poll,
            option=option,
            user=user,
            session_key=session_key,
            voter_token=voter_token
        )

    # Refresh options to return updated percentages and counts
    options = poll.options.all()
    total_votes = sum(o.vote_count for o in options)
    options_data = []
    for opt in options:
        pct = round((opt.vote_count / total_votes) * 100, 1) if total_votes > 0 else 0
        options_data.append({
            'id': opt.id,
            'text': opt.text,
            'vote_count': opt.vote_count,
            'percentage': pct,
            'is_selected': (opt.id == option.id),
        })

    response = JsonResponse({
        'success': True,
        'message': 'Oyunuz başarıyla kaydedildi!',
        'poll_id': poll.id,
        'total_votes': total_votes,
        'user_voted_option_id': option.id,
        'options': options_data,
    })
    response.set_cookie(COOKIE_VOTER_TOKEN_NAME, voter_token, max_age=COOKIE_MAX_AGE, samesite='Lax')
    return response


@login_required
@require_POST
def poll_toggle_status_view(request, poll_id):
    """
    Allows the poll author to toggle active/closed state of their poll.
    """
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.author != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Yalnızca anket sahibi bu işlemi yapabilir.'}, status=403)
        messages.error(request, 'Bu anketi kapatma yetkiniz yok.')
        return redirect('index')

    poll.is_active = not poll.is_active
    poll.save(update_fields=['is_active'])

    status_msg = "Anket yeniden oylamaya açıldı." if poll.is_active else "Anket oylamaya kapatıldı."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_active': poll.is_active,
            'is_closed': poll.is_closed,
            'status_label': poll.status_label,
            'message': status_msg
        })

    messages.success(request, status_msg)
    return redirect('index')


@login_required
@require_POST
def poll_delete_view(request, poll_id):
    """
    Allows the poll author to delete their poll permanently.
    """
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.author != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Yalnızca anket sahibi anketi silebilir.'}, status=403)
        messages.error(request, 'Bu anketi silme yetkiniz yok.')
        return redirect('index')

    question_preview = poll.question[:40]
    poll.delete()

    success_msg = f'"{question_preview}..." anketi başarıyla silindi.'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'poll_id': poll_id
        })

    messages.success(request, success_msg)
    return redirect('index')
