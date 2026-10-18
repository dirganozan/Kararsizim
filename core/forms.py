from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Poll


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='E-posta',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'ornek@email.com',
            'autocomplete': 'email'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'kullanici_adiniz',
            'autocomplete': 'username'
        })
        self.fields['username'].help_text = 'Harf, rakam ve @/./+/-/_ karakterleri içerebilir.'
        
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-input',
                'placeholder': '••••••••',
                'autocomplete': 'new-password'
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-input',
                'placeholder': '••••••••',
                'autocomplete': 'new-password'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Bu e-posta adresi ile zaten kayıtlı bir hesap var.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Kullanıcı Adı',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'kullanici_adiniz',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Şifre',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )


class PollCreateForm(forms.ModelForm):
    question = forms.CharField(
        label='Kararsız kaldığın soru nedir?',
        max_length=255,
        min_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Örn: Bugün sinemaya mı gitsem yoksa restorana mı?',
            'autocomplete': 'off',
            'autofocus': True
        }),
        error_messages={
            'required': 'Lütfen kararsız kaldığınız soruyu yazın.',
            'min_length': 'Soru metni en az 5 karakter olmalıdır.',
            'max_length': 'Soru metni en fazla 255 karakter olabilir.'
        }
    )

    class Meta:
        model = Poll
        fields = ('question',)

    def clean_question(self):
        question = self.cleaned_data.get('question', '').strip()
        if len(question) < 5:
            raise forms.ValidationError('Soru metni en az 5 karakter olmalıdır.')
        return question
