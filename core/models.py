from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
    Supports auto-expiration and manual closure by author.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='polls',
        verbose_name='Yazar'
    )
    question = models.CharField('Soru', max_length=255)
    is_active = models.BooleanField('Aktif mi?', default=True)
    expires_at = models.DateTimeField('Bitiş Tarihi', null=True, blank=True)
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

    @property
    def is_closed(self):
        """
        Poll is closed if author deactivated it OR expiration time has passed.
        """
        if not self.is_active:
            return True
        if self.expires_at and timezone.now() >= self.expires_at:
            return True
        return False

    @property
    def status_label(self):
        """
        Human-readable remaining time or closed status.
        """
        if not self.is_active:
            return "Oylama Kapandı (Yazar kapattı)"
        if self.expires_at:
            now = timezone.now()
            if now >= self.expires_at:
                return "Oylama Kapandı (Süre doldu)"
            diff = self.expires_at - now
            hours = int(diff.total_seconds() // 3600)
            minutes = int((diff.total_seconds() % 3600) // 60)
            if hours >= 24:
                days = hours // 24
                return f"⏳ {days} gün kaldı"
            elif hours > 0:
                return f"⏳ {hours}s {minutes}dk kaldı"
            else:
                return f"⏳ {max(1, minutes)}dk kaldı"
        return "⚡ Oylamaya açık (Süresiz)"


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
    Tracks which option was selected.
    Uses voter_token (persistent cookie) and session_key for rock-solid anonymous tracking.
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
    voter_token = models.CharField('Tarayıcı/Cihaz Belirteci', max_length=64, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField('Oy Tarihi', auto_now_add=True)

    class Meta:
        verbose_name = 'Oy Kaydı'
        verbose_name_plural = 'Oy Kayıtları'
        indexes = [
            models.Index(fields=['poll', 'user']),
            models.Index(fields=['poll', 'session_key']),
            models.Index(fields=['poll', 'voter_token']),
        ]

    def __str__(self):
        voter = f"@{self.user.username}" if self.user else f"Anonim ({self.voter_token or self.session_key})"
        return f"{voter} voted on Poll #{self.poll_id}"
