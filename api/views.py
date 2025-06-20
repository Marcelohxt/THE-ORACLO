from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json

from core.models import (
    Article, NewsSource, Category, Analysis, Alert, 
    CollectionLog, UserPreference
)
from core.serializers import (
    ArticleSerializer, NewsSourceSerializer, CategorySerializer,
    AnalysisSerializer, AlertSerializer, CollectionLogSerializer
)
# Removendo importação problemática temporariamente
# from news_collector.collectors import collect_from_source
from data_processor.processors import ProcessingManager


class ArticleViewSet(viewsets.ModelViewSet):
    """ViewSet para artigos"""
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source', 'categories', 'status', 'priority', 'is_breaking_news', 'is_featured']
    search_fields = ['title', 'content', 'author']
    ordering_fields = ['collected_date', 'published_date', 'sentiment_score', 'relevance_score']
    ordering = ['-collected_date']

    @action(detail=False, methods=['get'])
    def breaking_news(self, request):
        """Retorna notícias de última hora"""
        articles = self.queryset.filter(
            is_breaking_news=True,
            collected_date__gte=timezone.now() - timedelta(hours=24)
        )
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Retorna artigos em tendência"""
        # Artigos com mais visualizações nas últimas 24h
        articles = self.queryset.filter(
            collected_date__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-views_count', '-shares_count')
        serializer = self.get_serializer(articles[:20], many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_sentiment(self, request):
        """Retorna artigos por sentimento"""
        sentiment = request.query_params.get('sentiment', 'positive')
        
        if sentiment == 'positive':
            articles = self.queryset.filter(sentiment_score__gt=0.1)
        elif sentiment == 'negative':
            articles = self.queryset.filter(sentiment_score__lt=-0.1)
        else:
            articles = self.queryset.filter(
                sentiment_score__gte=-0.1,
                sentiment_score__lte=0.1
            )
        
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Analisa um artigo específico"""
        article = self.get_object()
        processor = ProcessingManager()
        
        # Executa análise assíncrona
        import asyncio
        results = asyncio.run(processor.process_article(article))
        
        return Response({
            'message': 'Análise iniciada',
            'article_id': article.id,
            'results': results
        })


class NewsSourceViewSet(viewsets.ModelViewSet):
    """ViewSet para fontes de notícias"""
    queryset = NewsSource.objects.all()
    serializer_class = NewsSourceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['source_type', 'country', 'language', 'is_active']
    search_fields = ['name', 'url']

    @action(detail=True, methods=['post'])
    def collect(self, request, pk=None):
        """Inicia coleta de uma fonte específica"""
        source = self.get_object()
        
        try:
            # Executa coleta assíncrona
            import asyncio
            # Temporariamente comentado até corrigir a importação
            # articles = asyncio.run(collect_from_source(source))
            
            return Response({
                'message': 'Coleta iniciada',
                'source_id': source.id,
                'articles_collected': 0  # Temporário
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas das fontes"""
        total_sources = NewsSource.objects.count()
        active_sources = NewsSource.objects.filter(is_active=True).count()
        
        # Últimas coletas
        recent_collections = CollectionLog.objects.filter(
            completed_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        return Response({
            'total_sources': total_sources,
            'active_sources': active_sources,
            'recent_collections': recent_collections
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para categorias"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    @action(detail=True, methods=['get'])
    def articles(self, request, pk=None):
        """Retorna artigos de uma categoria"""
        category = self.get_object()
        articles = Article.objects.filter(categories=category)
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)


class AnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet para análises"""
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['article', 'analysis_type']
    ordering = ['-created_at']


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet para alertas"""
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['alert_type', 'priority', 'is_active', 'is_read']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Marca alerta como lido"""
        alert = self.get_object()
        alert.is_read = True
        alert.read_at = timezone.now()
        alert.save()
        return Response({'message': 'Alerta marcado como lido'})


class CollectionLogViewSet(viewsets.ModelViewSet):
    """ViewSet para logs de coleta"""
    queryset = CollectionLog.objects.all()
    serializer_class = CollectionLogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['source', 'status']
    ordering = ['-started_at']


class StatsView(APIView):
    """View para estatísticas gerais"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        # Estatísticas gerais
        total_articles = Article.objects.count()
        articles_today = Article.objects.filter(
            collected_date__date=timezone.now().date()
        ).count()
        
        # Artigos por status
        status_stats = Article.objects.values('status').annotate(
            count=Count('id')
        )
        
        # Artigos por categoria
        category_stats = Category.objects.annotate(
            article_count=Count('articles')
        ).values('name', 'article_count')
        
        # Sentimento médio
        avg_sentiment = Article.objects.filter(
            sentiment_score__isnull=False
        ).aggregate(avg=Avg('sentiment_score'))
        
        # Fontes mais ativas
        active_sources = NewsSource.objects.annotate(
            article_count=Count('articles')
        ).order_by('-article_count')[:10]
        
        return Response({
            'total_articles': total_articles,
            'articles_today': articles_today,
            'status_distribution': list(status_stats),
            'category_distribution': list(category_stats),
            'average_sentiment': avg_sentiment['avg'],
            'most_active_sources': NewsSourceSerializer(active_sources, many=True).data
        })


class SearchView(APIView):
    """View para busca avançada"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        source = request.query_params.get('source', '')
        sentiment = request.query_params.get('sentiment', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        
        articles = Article.objects.all()
        
        # Filtros
        if query:
            articles = articles.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query) |
                Q(author__icontains=query)
            )
        
        if category:
            articles = articles.filter(categories__name=category)
        
        if source:
            articles = articles.filter(source__name=source)
        
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
        
        if date_from:
            articles = articles.filter(collected_date__gte=date_from)
        
        if date_to:
            articles = articles.filter(collected_date__lte=date_to)
        
        # Paginação
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        articles = articles.order_by('-collected_date')[start:end]
        
        serializer = ArticleSerializer(articles, many=True)
        
        return Response({
            'results': serializer.data,
            'total': articles.count(),
            'page': page,
            'page_size': page_size
        })


class TrendingView(APIView):
    """View para tendências"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        
        # Palavras-chave mais frequentes
        from django.db.models import Count
        keywords = []
        for article in Article.objects.filter(collected_date__gte=since):
            if article.keywords:
                keywords.extend(article.keywords)
        
        keyword_counts = {}
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        trending_keywords = sorted(
            keyword_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Entidades mais mencionadas
        entity_counts = {}
        for article in Article.objects.filter(collected_date__gte=since):
            if article.entities:
                for entity in article.entities:
                    entity_text = entity.get('text', '')
                    entity_counts[entity_text] = entity_counts.get(entity_text, 0) + 1
        
        trending_entities = sorted(
            entity_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Artigos mais compartilhados
        trending_articles = Article.objects.filter(
            collected_date__gte=since
        ).order_by('-shares_count', '-views_count')[:10]
        
        return Response({
            'trending_keywords': trending_keywords,
            'trending_entities': trending_entities,
            'trending_articles': ArticleSerializer(trending_articles, many=True).data
        })


class SentimentAnalysisView(APIView):
    """View para análise de sentimento"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response(
                {'error': 'Texto é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from data_processor.processors import SentimentProcessor
        processor = SentimentProcessor()
        result = processor.analyze_sentiment(text)
        
        return Response(result)


class EntityExtractionView(APIView):
    """View para extração de entidades"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response(
                {'error': 'Texto é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from data_processor.processors import EntityProcessor
        processor = EntityProcessor()
        entities = processor.extract_entities(text)
        
        return Response({'entities': entities})


class KeywordExtractionView(APIView):
    """View para extração de palavras-chave"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response(
                {'error': 'Texto é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from data_processor.processors import KeywordProcessor
        processor = KeywordProcessor()
        keywords = processor.extract_keywords(text)
        
        return Response({'keywords': keywords})


class QualityScoreView(APIView):
    """View para cálculo de score de qualidade"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        article_id = request.data.get('article_id')
        if not article_id:
            return Response(
                {'error': 'ID do artigo é obrigatório'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return Response(
                {'error': 'Artigo não encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        from data_processor.processors import QualityProcessor
        processor = QualityProcessor()
        quality_score = processor.calculate_quality_score(article)
        
        return Response(quality_score)


class CollectView(APIView):
    """View para iniciar coleta"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        source_id = request.data.get('source_id')
        if source_id:
            # Coleta de fonte específica
            try:
                source = NewsSource.objects.get(id=source_id)
                # Temporariamente comentado
                # import asyncio
                # articles = asyncio.run(collect_from_source(source))
                return Response({
                    'message': 'Coleta iniciada',
                    'articles_collected': 0  # Temporário
                })
            except NewsSource.DoesNotExist:
                return Response(
                    {'error': 'Fonte não encontrada'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Coleta de todas as fontes ativas
            sources = NewsSource.objects.filter(is_active=True)
            total_articles = 0
            
            # Temporariamente comentado
            # for source in sources:
            #     try:
            #         import asyncio
            #         articles = asyncio.run(collect_from_source(source))
            #         total_articles += len(articles)
            #     except Exception as e:
            #         logger.error(f"Erro ao coletar de {source.name}: {e}")
            
            return Response({
                'message': 'Coleta em lote iniciada',
                'sources_processed': sources.count(),
                'total_articles_collected': total_articles
            })


class ProcessView(APIView):
    """View para processar artigos"""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        article_id = request.data.get('article_id')
        batch_size = int(request.data.get('batch_size', 50))
        
        if article_id:
            # Processa artigo específico
            try:
                article = Article.objects.get(id=article_id)
                processor = ProcessingManager()
                import asyncio
                result = asyncio.run(processor.process_article(article))
                return Response({
                    'message': 'Processamento concluído',
                    'article_id': article_id,
                    'result': result
                })
            except Article.DoesNotExist:
                return Response(
                    {'error': 'Artigo não encontrado'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Processa lote de artigos não processados
            articles = Article.objects.filter(
                status='collected'
            )[:batch_size]
            
            processor = ProcessingManager()
            import asyncio
            result = asyncio.run(processor.process_batch(articles))
            
            return Response({
                'message': 'Processamento em lote concluído',
                'result': result
            })
