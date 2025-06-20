from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json

from core.models import (
    Article, NewsSource, Category, Analysis, Alert, 
    CollectionLog, UserPreference
)
from news_collector.models import CollectionTask
from data_processor.models import ProcessingTask, QualityScore


@login_required
def test_view(request):
    """View de teste para verificar templates"""
    return render(request, 'dashboard/test.html')


@login_required
def monitor_view(request):
    """Página de monitoramento em tempo real"""
    return render(request, 'dashboard/monitor.html')


@login_required
def dashboard_home(request):
    """Dashboard principal"""
    # Estatísticas gerais
    total_articles = Article.objects.count()
    articles_today = Article.objects.filter(
        collected_date__date=timezone.now().date()
    ).count()
    
    total_sources = NewsSource.objects.count()
    active_sources = NewsSource.objects.filter(is_active=True).count()
    
    # Artigos por status
    status_stats = Article.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Últimos artigos
    recent_articles = Article.objects.order_by('-collected_date')[:10]
    
    # Alertas não lidos
    unread_alerts = Alert.objects.filter(is_active=True, is_read=False).count()
    
    # Últimas coletas
    recent_collections = CollectionLog.objects.order_by('-started_at')[:5]
    
    # Sentimento médio
    avg_sentiment = Article.objects.filter(
        sentiment_score__isnull=False
    ).aggregate(avg=Avg('sentiment_score'))
    
    context = {
        'total_articles': total_articles,
        'articles_today': articles_today,
        'total_sources': total_sources,
        'active_sources': active_sources,
        'status_stats': status_stats,
        'recent_articles': recent_articles,
        'unread_alerts': unread_alerts,
        'recent_collections': recent_collections,
        'avg_sentiment': avg_sentiment['avg'] or 0,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def articles_list(request):
    """Lista de artigos"""
    articles = Article.objects.all()
    
    # Filtros
    category = request.GET.get('category')
    if category:
        articles = articles.filter(categories__name=category)
    
    source = request.GET.get('source')
    if source:
        articles = articles.filter(source__name=source)
    
    status = request.GET.get('status')
    if status:
        articles = articles.filter(status=status)
    
    sentiment = request.GET.get('sentiment')
    if sentiment:
        if sentiment == 'positive':
            articles = articles.filter(sentiment_score__gt=0.1)
        elif sentiment == 'negative':
            articles = articles.filter(sentiment_score__lt=-0.1)
        else:
            articles = articles.filter(
                sentiment_score__gte=-0.1,
                sentiment_score__lte=0.1
            )
    
    # Busca
    search = request.GET.get('search')
    if search:
        articles = articles.filter(
            Q(title__icontains=search) | 
            Q(content__icontains=search) |
            Q(author__icontains=search)
        )
    
    # Ordenação
    order_by = request.GET.get('order_by', '-collected_date')
    articles = articles.order_by(order_by)
    
    # Paginação
    from django.core.paginator import Paginator
    paginator = Paginator(articles, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtros disponíveis
    categories = Category.objects.all()
    sources = NewsSource.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'sources': sources,
        'filters': {
            'category': category,
            'source': source,
            'status': status,
            'sentiment': sentiment,
            'search': search,
            'order_by': order_by,
        }
    }
    
    return render(request, 'dashboard/articles_list.html', context)


@login_required
def article_detail(request, article_id):
    """Detalhes de um artigo"""
    article = get_object_or_404(Article, id=article_id)
    analyses = article.analyses.all()
    
    try:
        quality_score = article.quality_score
    except:
        quality_score = None
    
    context = {
        'article': article,
        'analyses': analyses,
        'quality_score': quality_score,
    }
    
    return render(request, 'dashboard/article_detail.html', context)


@login_required
def sources_list(request):
    """Lista de fontes de notícias"""
    sources = NewsSource.objects.all()
    
    # Filtros
    source_type = request.GET.get('source_type')
    if source_type:
        sources = sources.filter(source_type=source_type)
    
    is_active = request.GET.get('is_active')
    if is_active is not None:
        sources = sources.filter(is_active=is_active == 'true')
    
    # Busca
    search = request.GET.get('search')
    if search:
        sources = sources.filter(
            Q(name__icontains=search) | 
            Q(url__icontains=search)
        )
    
    # Ordenação
    order_by = request.GET.get('order_by', 'name')
    sources = sources.order_by(order_by)
    
    # Paginação
    from django.core.paginator import Paginator
    paginator = Paginator(sources, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filters': {
            'source_type': source_type,
            'is_active': is_active,
            'search': search,
            'order_by': order_by,
        }
    }
    
    return render(request, 'dashboard/sources_list.html', context)


@login_required
def source_detail(request, source_id):
    """Detalhes de uma fonte"""
    source = get_object_or_404(NewsSource, id=source_id)
    recent_articles = source.articles.order_by('-collected_date')[:20]
    collection_logs = source.collection_logs.order_by('-started_at')[:10]
    
    # Estatísticas da fonte
    total_articles = source.articles.count()
    articles_today = source.articles.filter(
        collected_date__date=timezone.now().date()
    ).count()
    
    avg_sentiment = source.articles.filter(
        sentiment_score__isnull=False
    ).aggregate(avg=Avg('sentiment_score'))
    
    context = {
        'source': source,
        'recent_articles': recent_articles,
        'collection_logs': collection_logs,
        'total_articles': total_articles,
        'articles_today': articles_today,
        'avg_sentiment': avg_sentiment['avg'] or 0,
    }
    
    return render(request, 'dashboard/source_detail.html', context)


@login_required
def categories_list(request):
    """Lista de categorias"""
    categories = Category.objects.all()
    
    # Busca
    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Ordenação
    order_by = request.GET.get('order_by', 'name')
    categories = categories.order_by(order_by)
    
    # Paginação
    from django.core.paginator import Paginator
    paginator = Paginator(categories, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filters': {
            'search': search,
            'order_by': order_by,
        }
    }
    
    return render(request, 'dashboard/categories_list.html', context)


@login_required
def category_detail(request, category_id):
    """Detalhes de uma categoria"""
    category = get_object_or_404(Category, id=category_id)
    recent_articles = category.articles.order_by('-collected_date')[:20]
    
    # Estatísticas da categoria
    total_articles = category.articles.count()
    articles_today = category.articles.filter(
        collected_date__date=timezone.now().date()
    ).count()
    
    avg_sentiment = category.articles.filter(
        sentiment_score__isnull=False
    ).aggregate(avg=Avg('sentiment_score'))
    
    # Distribuição de sentimento
    sentiment_distribution = {
        'positive': category.articles.filter(sentiment_score__gt=0.1).count(),
        'negative': category.articles.filter(sentiment_score__lt=-0.1).count(),
        'neutral': category.articles.filter(
            sentiment_score__gte=-0.1,
            sentiment_score__lte=0.1
        ).count(),
    }
    
    context = {
        'category': category,
        'recent_articles': recent_articles,
        'total_articles': total_articles,
        'articles_today': articles_today,
        'avg_sentiment': avg_sentiment['avg'] or 0,
        'sentiment_distribution': sentiment_distribution,
    }
    
    return render(request, 'dashboard/category_detail.html', context)


@login_required
def alerts_list(request):
    """Lista de alertas"""
    alerts = Alert.objects.all()
    
    # Filtros
    alert_type = request.GET.get('alert_type')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)
    
    priority = request.GET.get('priority')
    if priority:
        alerts = alerts.filter(priority=priority)
    
    is_read = request.GET.get('is_read')
    if is_read is not None:
        alerts = alerts.filter(is_read=is_read == 'true')
    
    # Ordenação
    order_by = request.GET.get('order_by', '-created_at')
    alerts = alerts.order_by(order_by)
    
    # Paginação
    from django.core.paginator import Paginator
    paginator = Paginator(alerts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filters': {
            'alert_type': alert_type,
            'priority': priority,
            'is_read': is_read,
            'order_by': order_by,
        }
    }
    
    return render(request, 'dashboard/alerts_list.html', context)


@login_required
def alert_detail(request, alert_id):
    """Detalhes de um alerta"""
    alert = get_object_or_404(Alert, id=alert_id)
    
    # Marca como lido se não estiver
    if not alert.is_read:
        alert.is_read = True
        alert.read_at = timezone.now()
        alert.save()
    
    context = {
        'alert': alert,
    }
    
    return render(request, 'dashboard/alert_detail.html', context)


@login_required
def analytics(request):
    """Página de análises e estatísticas"""
    # Período
    days = int(request.GET.get('days', 7))
    since = timezone.now() - timedelta(days=days)
    
    # Artigos por dia
    articles_per_day = []
    for i in range(days):
        date = timezone.now().date() - timedelta(days=i)
        count = Article.objects.filter(
            collected_date__date=date
        ).count()
        articles_per_day.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    articles_per_day.reverse()
    
    # Sentimento por dia
    sentiment_per_day = []
    for i in range(days):
        date = timezone.now().date() - timedelta(days=i)
        avg = Article.objects.filter(
            collected_date__date=date,
            sentiment_score__isnull=False
        ).aggregate(avg=Avg('sentiment_score'))
        sentiment_per_day.append({
            'date': date.strftime('%Y-%m-%d'),
            'sentiment': avg['avg'] or 0
        })
    sentiment_per_day.reverse()
    
    # Top categorias
    top_categories = Category.objects.annotate(
        article_count=Count('articles', filter=Q(articles__collected_date__gte=since))
    ).order_by('-article_count')[:10]
    
    # Top fontes
    top_sources = NewsSource.objects.annotate(
        article_count=Count('articles', filter=Q(articles__collected_date__gte=since))
    ).order_by('-article_count')[:10]
    
    # Palavras-chave mais frequentes
    keywords = {}
    for article in Article.objects.filter(collected_date__gte=since):
        if article.keywords:
            for keyword in article.keywords:
                keywords[keyword] = keywords.get(keyword, 0) + 1
    
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Entidades mais mencionadas
    entities = {}
    for article in Article.objects.filter(collected_date__gte=since):
        if article.entities:
            for entity in article.entities:
                entity_text = entity.get('text', '')
                entities[entity_text] = entities.get(entity_text, 0) + 1
    
    top_entities = sorted(entities.items(), key=lambda x: x[1], reverse=True)[:10]
    
    context = {
        'days': days,
        'articles_per_day': articles_per_day,
        'sentiment_per_day': sentiment_per_day,
        'top_categories': top_categories,
        'top_sources': top_sources,
        'top_keywords': top_keywords,
        'top_entities': top_entities,
    }
    
    return render(request, 'dashboard/analytics.html', context)


@login_required
def settings_view(request):
    """Configurações do sistema"""
    if request.method == 'POST':
        # Processa configurações
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('dashboard:settings')
    
    # Estatísticas do sistema
    total_articles = Article.objects.count()
    total_sources = NewsSource.objects.count()
    total_categories = Category.objects.count()
    
    # Status das coletas
    recent_collections = CollectionLog.objects.filter(
        started_at__gte=timezone.now() - timedelta(hours=24)
    )
    successful_collections = recent_collections.filter(status='success').count()
    failed_collections = recent_collections.filter(status='error').count()
    
    context = {
        'total_articles': total_articles,
        'total_sources': total_sources,
        'total_categories': total_categories,
        'recent_collections': recent_collections.count(),
        'successful_collections': successful_collections,
        'failed_collections': failed_collections,
    }
    
    return render(request, 'dashboard/settings.html', context)


@login_required
def api_docs(request):
    """Documentação da API"""
    return render(request, 'dashboard/api_docs.html')


# Views AJAX para atualizações em tempo real
@login_required
def ajax_stats(request):
    """Estatísticas atualizadas via AJAX"""
    total_articles = Article.objects.count()
    articles_today = Article.objects.filter(
        collected_date__date=timezone.now().date()
    ).count()
    
    unread_alerts = Alert.objects.filter(is_active=True, is_read=False).count()
    
    # Últimas coletas
    recent_collections = CollectionLog.objects.order_by('-started_at')[:5]
    collection_data = []
    for collection in recent_collections:
        collection_data.append({
            'source': collection.source.name,
            'status': collection.status,
            'articles_collected': collection.articles_collected,
            'started_at': collection.started_at.strftime('%H:%M'),
        })
    
    return JsonResponse({
        'total_articles': total_articles,
        'articles_today': articles_today,
        'unread_alerts': unread_alerts,
        'recent_collections': collection_data,
    })


@login_required
def ajax_recent_articles(request):
    """Artigos recentes via AJAX"""
    recent_articles = Article.objects.order_by('-collected_date')[:10]
    articles_data = []
    
    for article in recent_articles:
        articles_data.append({
            'id': article.id,
            'title': article.title,
            'source': article.source.name,
            'collected_date': article.collected_date.strftime('%H:%M'),
            'sentiment_score': article.sentiment_score,
            'is_breaking_news': article.is_breaking_news,
        })
    
    return JsonResponse({
        'articles': articles_data,
    })


@login_required
def ajax_collect_source(request, source_id):
    """Inicia coleta de uma fonte via AJAX"""
    source = get_object_or_404(NewsSource, id=source_id)
    
    try:
        # Aqui você chamaria a função de coleta
        # Por enquanto, apenas simula
        messages.success(request, f'Coleta iniciada para {source.name}')
        return JsonResponse({'status': 'success', 'message': 'Coleta iniciada'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def ajax_process_articles(request):
    """Processa artigos via AJAX"""
    try:
        # Aqui você chamaria a função de processamento
        # Por enquanto, apenas simula
        messages.success(request, 'Processamento iniciado')
        return JsonResponse({'status': 'success', 'message': 'Processamento iniciado'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
