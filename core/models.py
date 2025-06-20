from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid


class Category(models.Model):
    """Categorias de notícias"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class NewsSource(models.Model):
    """Fontes de notícias"""
    SOURCE_TYPES = [
        ('website', 'Website'),
        ('rss', 'RSS Feed'),
        ('api', 'API'),
        ('social', 'Social Media'),
        ('telegram', 'Telegram Channel'),
    ]

    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='website')
    country = models.CharField(max_length=3, blank=True)  # ISO country code
    language = models.CharField(max_length=5, default='pt-BR')  # ISO language code
    categories = models.ManyToManyField(Category, blank=True)
    is_active = models.BooleanField(default=True)
    last_collection = models.DateTimeField(null=True, blank=True)
    collection_interval = models.IntegerField(default=300)  # seconds
    max_articles = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.source_type})"


class Article(models.Model):
    """Artigos coletados"""
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]

    STATUS_CHOICES = [
        ('collected', 'Coletado'),
        ('processed', 'Processado'),
        ('analyzed', 'Analisado'),
        ('published', 'Publicado'),
        ('archived', 'Arquivado'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=500)
    content = models.TextField()
    summary = models.TextField(blank=True)
    url = models.URLField(max_length=1000, unique=True)
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='articles')
    categories = models.ManyToManyField(Category, blank=True)
    
    # Metadata
    author = models.CharField(max_length=200, blank=True)
    published_date = models.DateTimeField(null=True, blank=True)
    collected_date = models.DateTimeField(auto_now_add=True)
    
    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    entities = models.JSONField(default=list, blank=True)
    
    # Engagement
    views_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    
    # Flags
    is_breaking_news = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-collected_date']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['collected_date']),
            models.Index(fields=['source', 'collected_date']),
        ]

    def __str__(self):
        return self.title[:100]

    @property
    def age_hours(self):
        """Retorna a idade do artigo em horas"""
        return (timezone.now() - self.collected_date).total_seconds() / 3600


class Analysis(models.Model):
    """Análises de artigos"""
    ANALYSIS_TYPES = [
        ('sentiment', 'Análise de Sentimento'),
        ('entities', 'Extração de Entidades'),
        ('keywords', 'Extração de Palavras-chave'),
        ('summary', 'Resumo Automático'),
        ('classification', 'Classificação'),
        ('ai_insight', 'Insight IA'),
    ]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    result = models.JSONField()
    confidence = models.FloatField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['article', 'analysis_type']

    def __str__(self):
        return f"{self.article.title[:50]} - {self.analysis_type}"


class Alert(models.Model):
    """Alertas e notificações"""
    ALERT_TYPES = [
        ('breaking_news', 'Notícia de Última Hora'),
        ('trending', 'Tendência'),
        ('sentiment_change', 'Mudança de Sentimento'),
        ('volume_spike', 'Pico de Volume'),
        ('keyword_match', 'Palavra-chave Detectada'),
        ('source_offline', 'Fonte Offline'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Related data
    articles = models.ManyToManyField(Article, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alert_type}: {self.title}"


class CollectionLog(models.Model):
    """Log de coletas de dados"""
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='collection_logs')
    status = models.CharField(max_length=20, choices=[
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('partial', 'Parcial'),
    ])
    articles_collected = models.IntegerField(default=0)
    articles_processed = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # seconds
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.source.name} - {self.status} ({self.articles_collected} artigos)"


class UserPreference(models.Model):
    """Preferências do usuário"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    categories = models.ManyToManyField(Category, blank=True)
    sources = models.ManyToManyField(NewsSource, blank=True)
    alert_types = models.JSONField(default=list, blank=True)
    notification_email = models.BooleanField(default=True)
    notification_telegram = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=5, default='pt-BR')
    timezone = models.CharField(max_length=50, default='America/Sao_Paulo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferências de {self.user.username}"
