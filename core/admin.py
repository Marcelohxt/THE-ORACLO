from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import (
    Category, NewsSource, Article, Analysis, Alert, 
    CollectionLog, UserPreference
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'article_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = 'Artigos'


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'source_type', 'country', 'is_active', 
        'article_count', 'last_collection', 'collection_status'
    ]
    list_filter = ['source_type', 'country', 'language', 'is_active', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['created_at', 'updated_at', 'last_collection']
    filter_horizontal = ['categories']
    
    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = 'Artigos'
    
    def collection_status(self, obj):
        if obj.last_collection:
            from django.utils import timezone
            from datetime import timedelta
            
            hours_ago = (timezone.now() - obj.last_collection).total_seconds() / 3600
            if hours_ago < 1:
                return format_html('<span style="color: green;">✓ Ativo</span>')
            elif hours_ago < 24:
                return format_html('<span style="color: orange;">⚠ {:.0f}h atrás</span>', hours_ago)
            else:
                return format_html('<span style="color: red;">✗ {:.0f}h atrás</span>', hours_ago)
        return format_html('<span style="color: gray;">Nunca</span>')
    collection_status.short_description = 'Status'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'source', 'status', 'priority', 'sentiment_display',
        'collected_date', 'is_breaking_news', 'is_featured'
    ]
    list_filter = [
        'status', 'priority', 'is_breaking_news', 'is_featured', 
        'is_verified', 'collected_date', 'source'
    ]
    search_fields = ['title', 'content', 'author', 'url']
    readonly_fields = ['uuid', 'collected_date', 'sentiment_score', 'relevance_score']
    filter_horizontal = ['categories']
    date_hierarchy = 'collected_date'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'content', 'summary', 'url', 'source', 'categories')
        }),
        ('Metadados', {
            'fields': ('author', 'published_date', 'collected_date', 'uuid')
        }),
        ('Processamento', {
            'fields': ('status', 'priority', 'sentiment_score', 'relevance_score')
        }),
        ('Análise', {
            'fields': ('keywords', 'entities', 'views_count', 'shares_count')
        }),
        ('Flags', {
            'fields': ('is_breaking_news', 'is_featured', 'is_verified')
        }),
    )
    
    def sentiment_display(self, obj):
        if obj.sentiment_score is None:
            return format_html('<span style="color: gray;">-</span>')
        elif obj.sentiment_score > 0.1:
            return format_html(
                '<span style="color: green;">{:.2f} (Positivo)</span>', 
                obj.sentiment_score
            )
        elif obj.sentiment_score < -0.1:
            return format_html(
                '<span style="color: red;">{:.2f} (Negativo)</span>', 
                obj.sentiment_score
            )
        else:
            return format_html(
                '<span style="color: blue;">{:.2f} (Neutro)</span>', 
                obj.sentiment_score
            )
    sentiment_display.short_description = 'Sentimento'
    
    actions = ['mark_as_processed', 'mark_as_analyzed', 'mark_as_featured']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(status='processed')
        self.message_user(request, f'{queryset.count()} artigos marcados como processados.')
    mark_as_processed.short_description = 'Marcar como processados'
    
    def mark_as_analyzed(self, request, queryset):
        queryset.update(status='analyzed')
        self.message_user(request, f'{queryset.count()} artigos marcados como analisados.')
    mark_as_analyzed.short_description = 'Marcar como analisados'
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} artigos marcados como destaque.')
    mark_as_featured.short_description = 'Marcar como destaque'


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['article', 'analysis_type', 'confidence', 'processing_time', 'created_at']
    list_filter = ['analysis_type', 'created_at']
    search_fields = ['article__title']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'alert_type', 'priority', 'is_active', 
        'is_read', 'created_at'
    ]
    list_filter = ['alert_type', 'priority', 'is_active', 'is_read', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'read_at']
    filter_horizontal = ['articles', 'categories']
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{queryset.count()} alertas marcados como lidos.')
    mark_as_read.short_description = 'Marcar como lidos'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{queryset.count()} alertas marcados como não lidos.')
    mark_as_unread.short_description = 'Marcar como não lidos'


@admin.register(CollectionLog)
class CollectionLogAdmin(admin.ModelAdmin):
    list_display = [
        'source', 'status', 'articles_collected', 'articles_processed',
        'processing_time', 'started_at', 'completed_at'
    ]
    list_filter = ['status', 'started_at', 'source']
    search_fields = ['source__name']
    readonly_fields = ['started_at', 'completed_at', 'processing_time']
    date_hierarchy = 'started_at'
    
    def processing_time(self, obj):
        if obj.processing_time:
            return f"{obj.processing_time:.2f}s"
        return "-"
    processing_time.short_description = 'Tempo de Processamento'


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_email', 'notification_telegram', 'language', 'timezone']
    list_filter = ['notification_email', 'notification_telegram', 'language', 'timezone']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['categories', 'sources']
    readonly_fields = ['created_at', 'updated_at']


# Configurações do admin
admin.site.site_header = "ORACLO - Administração"
admin.site.site_title = "ORACLO Admin"
admin.site.index_title = "Bem-vindo ao ORACLO"

# Adiciona estatísticas ao dashboard
class ORACLOAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Estatísticas gerais
        extra_context['total_articles'] = Article.objects.count()
        extra_context['total_sources'] = NewsSource.objects.count()
        extra_context['total_categories'] = Category.objects.count()
        extra_context['unread_alerts'] = Alert.objects.filter(is_read=False).count()
        
        # Artigos por status
        status_stats = Article.objects.values('status').annotate(count=Count('id'))
        extra_context['status_stats'] = status_stats
        
        # Últimos artigos
        extra_context['recent_articles'] = Article.objects.order_by('-collected_date')[:5]
        
        # Últimas coletas
        extra_context['recent_collections'] = CollectionLog.objects.order_by('-started_at')[:5]
        
        return super().index(request, extra_context)
