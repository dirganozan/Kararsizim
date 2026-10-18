from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Poll, Option, VoteLog
from .forms import RegisterForm, LoginForm, PollCreateForm


def index_view(request):
    """
    Main home page view.
    Lists polls in chronological order (newest first).
    """
    polls = Poll.objects.prefetch_related('options', 'author').all()
    poll_form = PollCreateForm() if request.user.is_authenticated else None

    context = {
        'page_title': 'Ana Sayfa - Kararsız kaldığın her şey burada!',
        'polls': polls,
        'poll_form': poll_form,
    }
    return render(request, 'core/index.html', context)


def register_view(request):
    """
    User registration view.
    Ensures username, email, and password are provided.
    """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Hoş geldin @{user.username}! Hesabın başarıyla oluşturuldu.')
            return redirect('index')
        else:
            messages.error(request, 'Lütfen formdaki hataları düzeltin.')
    else:
        form = RegisterForm()

    return render(request, 'core/register.html', {'form': form, 'page_title': 'Kayıt Ol'})


def login_view(request):
    """
    User login view.
    """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
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
    Supports both standard form submission and AJAX modal submission.
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
