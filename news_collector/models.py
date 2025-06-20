from django.db import models
from core.models import NewsSource, Article
import json


class ScrapingConfig(models.Model):
    """Configurações de scraping para fontes específicas"""
    source = models.OneToOneField(NewsSource, on_delete=models.CASCADE, related_name='scraping_config')
    
    # Selectors CSS/XPath
    title_selector = models.CharField(max_length=200, blank=True)
    content_selector = models.CharField(max_length=200, blank=True)
    author_selector = models.CharField(max_length=200, blank=True)
    date_selector = models.CharField(max_length=200, blank=True)
    image_selector = models.CharField(max_length=200, blank=True)
    
    # RSS specific
    rss_feed_url = models.URLField(max_length=500, blank=True)
    
    # API specific
    api_endpoint = models.URLField(max_length=500, blank=True)
    api_key = models.CharField(max_length=200, blank=True)
    api_headers = models.JSONField(default=dict, blank=True)
    
    # Processing
    content_cleanup_rules = models.JSONField(default=list, blank=True)
    date_format = models.CharField(max_length=50, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    # Rate limiting
    request_delay = models.FloatField(default=1.0)  # seconds
    max_requests_per_minute = models.IntegerField(default=60)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Config: {self.source.name}"


class CollectionTask(models.Model):
    """Tarefas de coleta agendadas"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('running', 'Executando'),
        ('completed', 'Concluída'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelada'),
    ]

    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='collection_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    articles_found = models.IntegerField(default=0)
    articles_collected = models.IntegerField(default=0)
    articles_updated = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    
    # Performance
    processing_time = models.FloatField(null=True, blank=True)  # seconds
    memory_usage = models.FloatField(null=True, blank=True)  # MB
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Task: {self.source.name} - {self.status}"


class RSSFeed(models.Model):
    """Feeds RSS configurados"""
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='rss_feeds')
    feed_url = models.URLField(max_length=500)
    feed_title = models.CharField(max_length=200, blank=True)
    feed_description = models.TextField(blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    etag = models.CharField(max_length=200, blank=True)
    last_modified = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['source', 'feed_url']

    def __str__(self):
        return f"RSS: {self.feed_title or self.feed_url}"


class SocialMediaSource(models.Model):
    """Fontes de redes sociais"""
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter/X'),
        ('telegram', 'Telegram'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
    ]

    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='social_sources')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    account_id = models.CharField(max_length=200)
    account_name = models.CharField(max_length=200, blank=True)
    
    # API credentials
    api_key = models.CharField(max_length=200, blank=True)
    api_secret = models.CharField(max_length=200, blank=True)
    access_token = models.CharField(max_length=200, blank=True)
    access_secret = models.CharField(max_length=200, blank=True)
    
    # Collection settings
    max_posts = models.IntegerField(default=100)
    include_retweets = models.BooleanField(default=False)
    include_replies = models.BooleanField(default=False)
    
    last_collection = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['source', 'platform', 'account_id']

    def __str__(self):
        return f"{self.platform}: {self.account_name or self.account_id}"


class WebhookEndpoint(models.Model):
    """Endpoints para webhooks de notícias"""
    name = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    secret_key = models.CharField(max_length=200, blank=True)
    
    # Configuration
    events = models.JSONField(default=list, blank=True)  # ['article.created', 'alert.triggered']
    is_active = models.BooleanField(default=True)
    retry_count = models.IntegerField(default=3)
    timeout = models.IntegerField(default=30)  # seconds
    
    # Statistics
    total_calls = models.IntegerField(default=0)
    successful_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    last_called = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Webhook: {self.name}"


class ProxyConfig(models.Model):
    """Configurações de proxy para coleta"""
    PROXY_TYPES = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
        ('socks4', 'SOCKS4'),
        ('socks5', 'SOCKS5'),
    ]

    name = models.CharField(max_length=200)
    proxy_type = models.CharField(max_length=10, choices=PROXY_TYPES)
    host = models.CharField(max_length=200)
    port = models.IntegerField()
    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=200, blank=True)
    
    # Usage
    is_active = models.BooleanField(default=True)
    is_rotating = models.BooleanField(default=False)
    max_requests = models.IntegerField(default=1000)
    current_requests = models.IntegerField(default=0)
    
    # Performance
    response_time = models.FloatField(null=True, blank=True)  # seconds
    success_rate = models.FloatField(default=100.0)  # percentage
    last_used = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Proxy: {self.name} ({self.host}:{self.port})"
