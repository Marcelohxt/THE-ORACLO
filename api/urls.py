from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet)
router.register(r'sources', views.NewsSourceViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'analyses', views.AnalysisViewSet)
router.register(r'alerts', views.AlertViewSet)
router.register(r'collection-logs', views.CollectionLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.StatsView.as_view(), name='api-stats'),
    path('search/', views.SearchView.as_view(), name='api-search'),
    path('trending/', views.TrendingView.as_view(), name='api-trending'),
    path('sentiment-analysis/', views.SentimentAnalysisView.as_view(), name='api-sentiment'),
    path('entity-extraction/', views.EntityExtractionView.as_view(), name='api-entities'),
    path('keyword-extraction/', views.KeywordExtractionView.as_view(), name='api-keywords'),
    path('quality-score/', views.QualityScoreView.as_view(), name='api-quality'),
    path('collect/', views.CollectView.as_view(), name='api-collect'),
    path('process/', views.ProcessView.as_view(), name='api-process'),
] 