from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for Krarsızım.
    Ensures email is unique and required.
    """
    email = models.EmailField(
        'E-posta Adresi',
        unique=True,
        blank=False,
        error_messages={
            'unique': 'Bu e-posta adresi ile zaten kayıtlı bir hesap var.',
        }
    )

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"@{self.username}"


class Poll(models.Model):
    """
    Poll model representing a decision dilemma.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='polls',
        verbose_name='Yazar'
    )
    question = models.CharField('Soru', max_length=255)
    created_at = models.DateTimeField('Oluşturulma Tarihi', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Anket'
        verbose_name_plural = 'Anketler'

    def __str__(self):
        return f"{self.question} (by @{self.author.username})"

    @property
    def total_votes(self):
        return sum(option.vote_count for option in self.options.all())


class Option(models.Model):
    """
    Poll option choice. A poll must have between 2 and 5 options.
    """
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='Anket'
    )
    text = models.CharField('Seçenek Metni', max_length=120)
    vote_count = models.PositiveIntegerField('Oy Sayısı', default=0)

    class Meta:
        verbose_name = 'Seçenek'
        verbose_name_plural = 'Seçenekler'

    def __str__(self):
        return f"{self.text} ({self.vote_count} oy)"

    def get_percentage(self, total=None):
        if total is None:
            total = self.poll.total_votes
        if total == 0:
            return 0
        return round((self.vote_count / total) * 100, 1)


class VoteLog(models.Model):
    """
    Log of votes to prevent duplicate votes by members or anonymous visitors.
    Tracks which option was selected as agreed in Phase 1 plan.
    """
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='vote_logs',
        verbose_name='Anket'
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vote_logs',
        verbose_name='Seçilen Seçenek'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vote_logs',
        verbose_name='Kullanıcı'
    )
    session_key = models.CharField('Oturum Anahtarı (Anonim)', max_length=40, null=True, blank=True)
    created_at = models.DateTimeField('Oy Tarihi', auto_now_add=True)

    class Meta:
        verbose_name = 'Oy Kaydı'
        verbose_name_plural = 'Oy Kayıtları'
        indexes = [
            models.Index(fields=['poll', 'user']),
            models.Index(fields=['poll', 'session_key']),
        ]

    def __str__(self):
        voter = f"@{self.user.username}" if self.user else f"Anonim ({self.session_key})"
        return f"{voter} voted on Poll #{self.poll_id}"
