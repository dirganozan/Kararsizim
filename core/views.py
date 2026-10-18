from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm, LoginForm


def index_view(request):
    """
    Main home page view.
    In Faz 1, displays welcome hero and authentication status.
    In Faz 2 and 3, will display the chronological feed of polls.
    """
    context = {
        'page_title': 'Ana Sayfa - Kararsız kaldığın her şey burada!',
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
