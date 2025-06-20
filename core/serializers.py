from rest_framework import serializers
from .models import (
    Category, NewsSource, Article, Analysis, Alert, 
    CollectionLog, UserPreference
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para categorias"""
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'color', 
            'is_active', 'created_at', 'updated_at', 'article_count'
        ]
    
    def get_article_count(self, obj):
        return obj.articles.count()


class NewsSourceSerializer(serializers.ModelSerializer):
    """Serializer para fontes de notícias"""
    categories = CategorySerializer(many=True, read_only=True)
    article_count = serializers.SerializerMethodField()
    last_collection_status = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsSource
        fields = [
            'id', 'name', 'url', 'source_type', 'country', 'language',
            'categories', 'is_active', 'last_collection', 'collection_interval',
            'max_articles', 'created_at', 'updated_at', 'article_count',
            'last_collection_status'
        ]
    
    def get_article_count(self, obj):
        return obj.articles.count()
    
    def get_last_collection_status(self, obj):
        last_log = obj.collection_logs.order_by('-started_at').first()
        return last_log.status if last_log else None


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer para artigos"""
    source = NewsSourceSerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    age_hours = serializers.ReadOnlyField()
    sentiment_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'uuid', 'title', 'content', 'summary', 'url', 'source',
            'categories', 'author', 'published_date', 'collected_date',
            'status', 'priority', 'sentiment_score', 'relevance_score',
            'keywords', 'entities', 'views_count', 'shares_count',
            'is_breaking_news', 'is_featured', 'is_verified', 'age_hours',
            'sentiment_label'
        ]
    
    def get_sentiment_label(self, obj):
        if obj.sentiment_score is None:
            return 'neutral'
        elif obj.sentiment_score > 0.1:
            return 'positive'
        elif obj.sentiment_score < -0.1:
            return 'negative'
        else:
            return 'neutral'


class AnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análises"""
    article = ArticleSerializer(read_only=True)
    
    class Meta:
        model = Analysis
        fields = [
            'id', 'article', 'analysis_type', 'result', 'confidence',
            'processing_time', 'created_at'
        ]


class AlertSerializer(serializers.ModelSerializer):
    """Serializer para alertas"""
    articles = ArticleSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'message', 'alert_type', 'priority',
            'articles', 'categories', 'is_active', 'is_read',
            'created_at', 'read_at'
        ]


class CollectionLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de coleta"""
    source = NewsSourceSerializer(read_only=True)
    processing_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CollectionLog
        fields = [
            'id', 'source', 'status', 'articles_collected', 'articles_processed',
            'errors', 'processing_time', 'started_at', 'completed_at',
            'processing_duration'
        ]
    
    def get_processing_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer para preferências do usuário"""
    categories = CategorySerializer(many=True, read_only=True)
    sources = NewsSourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = UserPreference
        fields = [
            'id', 'user', 'categories', 'sources', 'alert_types',
            'notification_email', 'notification_telegram', 'telegram_chat_id',
            'language', 'timezone', 'created_at', 'updated_at'
        ]


class ArticleDetailSerializer(ArticleSerializer):
    """Serializer detalhado para artigos"""
    analyses = AnalysisSerializer(many=True, read_only=True)
    quality_score = serializers.SerializerMethodField()
    
    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields + ['analyses', 'quality_score']
    
    def get_quality_score(self, obj):
        try:
            quality = obj.quality_score
            return {
                'overall_score': quality.overall_score,
                'readability_score': quality.readability_score,
                'completeness_score': quality.completeness_score,
                'accuracy_score': quality.accuracy_score,
                'relevance_score': quality.relevance_score,
                'factors': quality.factors
            }
        except:
            return None


class NewsSourceDetailSerializer(NewsSourceSerializer):
    """Serializer detalhado para fontes de notícias"""
    recent_articles = serializers.SerializerMethodField()
    collection_logs = CollectionLogSerializer(many=True, read_only=True)
    
    class Meta(NewsSourceSerializer.Meta):
        fields = NewsSourceSerializer.Meta.fields + ['recent_articles', 'collection_logs']
    
    def get_recent_articles(self, obj):
        recent = obj.articles.order_by('-collected_date')[:10]
        return ArticleSerializer(recent, many=True).data


class CategoryDetailSerializer(CategorySerializer):
    """Serializer detalhado para categorias"""
    recent_articles = serializers.SerializerMethodField()
    sentiment_distribution = serializers.SerializerMethodField()
    
    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['recent_articles', 'sentiment_distribution']
    
    def get_recent_articles(self, obj):
        recent = obj.articles.order_by('-collected_date')[:10]
        return ArticleSerializer(recent, many=True).data
    
    def get_sentiment_distribution(self, obj):
        articles = obj.articles.filter(sentiment_score__isnull=False)
        
        positive = articles.filter(sentiment_score__gt=0.1).count()
        negative = articles.filter(sentiment_score__lt=-0.1).count()
        neutral = articles.filter(
            sentiment_score__gte=-0.1,
            sentiment_score__lte=0.1
        ).count()
        
        total = articles.count()
        
        return {
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'total': total,
            'positive_percentage': (positive / total * 100) if total > 0 else 0,
            'negative_percentage': (negative / total * 100) if total > 0 else 0,
            'neutral_percentage': (neutral / total * 100) if total > 0 else 0,
        }


class StatsSerializer(serializers.Serializer):
    """Serializer para estatísticas"""
    total_articles = serializers.IntegerField()
    articles_today = serializers.IntegerField()
    total_sources = serializers.IntegerField()
    active_sources = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    average_sentiment = serializers.FloatField()
    recent_collections = serializers.IntegerField()
    processing_queue = serializers.IntegerField()
    
    # Distribuições
    status_distribution = serializers.ListField()
    category_distribution = serializers.ListField()
    source_distribution = serializers.ListField()
    sentiment_distribution = serializers.DictField()
    
    # Tendências
    articles_per_hour = serializers.ListField()
    sentiment_trend = serializers.ListField()
    top_keywords = serializers.ListField()
    top_entities = serializers.ListField()


class SearchResultSerializer(serializers.Serializer):
    """Serializer para resultados de busca"""
    results = ArticleSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    query = serializers.CharField()
    filters = serializers.DictField()


class TrendingSerializer(serializers.Serializer):
    """Serializer para tendências"""
    trending_keywords = serializers.ListField()
    trending_entities = serializers.ListField()
    trending_articles = ArticleSerializer(many=True)
    trending_topics = serializers.ListField()
    sentiment_trends = serializers.DictField()


class ProcessingResultSerializer(serializers.Serializer):
    """Serializer para resultados de processamento"""
    total_processed = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    processing_time = serializers.FloatField()
    errors = serializers.ListField()
    results = serializers.DictField()


class CollectionResultSerializer(serializers.Serializer):
    """Serializer para resultados de coleta"""
    source_id = serializers.IntegerField()
    source_name = serializers.CharField()
    articles_found = serializers.IntegerField()
    articles_collected = serializers.IntegerField()
    articles_updated = serializers.IntegerField()
    processing_time = serializers.FloatField()
    errors = serializers.ListField()
    status = serializers.CharField() 