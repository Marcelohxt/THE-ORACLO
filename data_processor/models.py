from django.db import models
from core.models import Article, Category
import json


class ProcessingPipeline(models.Model):
    """Pipelines de processamento de dados"""
    PIPELINE_TYPES = [
        ('text_cleaning', 'Limpeza de Texto'),
        ('sentiment_analysis', 'Análise de Sentimento'),
        ('entity_extraction', 'Extração de Entidades'),
        ('keyword_extraction', 'Extração de Palavras-chave'),
        ('classification', 'Classificação'),
        ('summarization', 'Resumo'),
        ('translation', 'Tradução'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    pipeline_type = models.CharField(max_length=30, choices=PIPELINE_TYPES)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=5)  # 1-10, higher = more priority
    batch_size = models.IntegerField(default=50)
    
    # Processing rules
    rules = models.JSONField(default=list, blank=True)
    filters = models.JSONField(default=list, blank=True)
    
    # Performance
    avg_processing_time = models.FloatField(null=True, blank=True)  # seconds
    success_rate = models.FloatField(default=100.0)  # percentage
    total_processed = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'name']

    def __str__(self):
        return f"Pipeline: {self.name} ({self.pipeline_type})"


class ProcessingRule(models.Model):
    """Regras de processamento"""
    RULE_TYPES = [
        ('text_filter', 'Filtro de Texto'),
        ('regex_replace', 'Substituição Regex'),
        ('html_clean', 'Limpeza HTML'),
        ('language_detect', 'Detecção de Idioma'),
        ('duplicate_check', 'Verificação de Duplicatas'),
        ('quality_score', 'Score de Qualidade'),
        ('spam_detect', 'Detecção de Spam'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=30, choices=RULE_TYPES)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=5)
    
    # Rule parameters
    parameters = models.JSONField(default=dict, blank=True)
    conditions = models.JSONField(default=list, blank=True)
    
    # Statistics
    total_applied = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'name']

    def __str__(self):
        return f"Rule: {self.name} ({self.rule_type})"


class ContentFilter(models.Model):
    """Filtros de conteúdo"""
    FILTER_TYPES = [
        ('keyword', 'Palavra-chave'),
        ('regex', 'Expressão Regular'),
        ('category', 'Categoria'),
        ('source', 'Fonte'),
        ('date_range', 'Intervalo de Data'),
        ('sentiment', 'Sentimento'),
        ('language', 'Idioma'),
        ('length', 'Tamanho do Texto'),
        ('quality', 'Qualidade'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_inclusive = models.BooleanField(default=True)  # True = include, False = exclude
    
    # Filter parameters
    parameters = models.JSONField(default=dict, blank=True)
    conditions = models.JSONField(default=list, blank=True)
    
    # Categories this filter applies to
    categories = models.ManyToManyField(Category, blank=True)
    
    # Statistics
    total_filtered = models.IntegerField(default=0)
    matched_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"Filter: {self.name} ({self.filter_type})"


class SentimentModel(models.Model):
    """Modelos de análise de sentimento"""
    MODEL_TYPES = [
        ('vader', 'VADER'),
        ('textblob', 'TextBlob'),
        ('transformers', 'Transformers'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    
    # Model configuration
    model_path = models.CharField(max_length=500, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    
    # Languages supported
    languages = models.JSONField(default=list, blank=True)
    
    # Performance
    accuracy = models.FloatField(null=True, blank=True)
    avg_processing_time = models.FloatField(null=True, blank=True)
    total_processed = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"Sentiment Model: {self.name} ({self.model_type})"


class EntityExtractor(models.Model):
    """Extratores de entidades nomeadas"""
    EXTRACTOR_TYPES = [
        ('spacy', 'spaCy'),
        ('nltk', 'NLTK'),
        ('transformers', 'Transformers'),
        ('regex', 'Regex'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    extractor_type = models.CharField(max_length=20, choices=EXTRACTOR_TYPES)
    
    # Configuration
    model_path = models.CharField(max_length=500, blank=True)
    entity_types = models.JSONField(default=list, blank=True)  # ['PERSON', 'ORG', 'LOC']
    parameters = models.JSONField(default=dict, blank=True)
    
    # Languages supported
    languages = models.JSONField(default=list, blank=True)
    
    # Performance
    avg_processing_time = models.FloatField(null=True, blank=True)
    total_processed = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"Entity Extractor: {self.name} ({self.extractor_type})"


class KeywordExtractor(models.Model):
    """Extratores de palavras-chave"""
    EXTRACTOR_TYPES = [
        ('tfidf', 'TF-IDF'),
        ('yake', 'YAKE'),
        ('rake', 'RAKE'),
        ('textrank', 'TextRank'),
        ('spacy', 'spaCy'),
        ('custom', 'Personalizado'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    extractor_type = models.CharField(max_length=20, choices=EXTRACTOR_TYPES)
    
    # Configuration
    parameters = models.JSONField(default=dict, blank=True)
    max_keywords = models.IntegerField(default=10)
    min_keyword_length = models.IntegerField(default=3)
    
    # Stop words and filters
    stop_words = models.JSONField(default=list, blank=True)
    custom_filters = models.JSONField(default=list, blank=True)
    
    # Languages supported
    languages = models.JSONField(default=list, blank=True)
    
    # Performance
    avg_processing_time = models.FloatField(null=True, blank=True)
    total_processed = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"Keyword Extractor: {self.name} ({self.extractor_type})"


class ProcessingTask(models.Model):
    """Tarefas de processamento"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('running', 'Executando'),
        ('completed', 'Concluída'),
        ('failed', 'Falhou'),
        ('cancelled', 'Cancelada'),
    ]

    pipeline = models.ForeignKey(ProcessingPipeline, on_delete=models.CASCADE, related_name='tasks')
    articles = models.ManyToManyField(Article, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Scheduling
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_articles = models.IntegerField(default=0)
    processed_articles = models.IntegerField(default=0)
    failed_articles = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    
    # Performance
    processing_time = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Task: {self.pipeline.name} - {self.status}"


class QualityScore(models.Model):
    """Scores de qualidade para artigos"""
    article = models.OneToOneField(Article, on_delete=models.CASCADE, related_name='quality_score')
    
    # Quality metrics
    readability_score = models.FloatField(null=True, blank=True)
    completeness_score = models.FloatField(null=True, blank=True)
    accuracy_score = models.FloatField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    
    # Overall score
    overall_score = models.FloatField(null=True, blank=True)
    
    # Factors
    factors = models.JSONField(default=dict, blank=True)
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Quality: {self.article.title[:50]} - {self.overall_score}"


class DuplicateGroup(models.Model):
    """Grupos de artigos duplicados"""
    title_similarity = models.FloatField(default=0.0)
    content_similarity = models.FloatField(default=0.0)
    url_similarity = models.FloatField(default=0.0)
    
    # Articles in this group
    articles = models.ManyToManyField(Article, related_name='duplicate_groups')
    
    # Best article (canonical)
    canonical_article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='canonical_for')
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolution_method = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Duplicate Group: {self.articles.count()} articles"
