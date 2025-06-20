from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_home, name='home'),
    path('monitor/', views.monitor_view, name='monitor'),
    
    # Artigos
    path('articles/', views.articles_list, name='articles_list'),
    path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
    
    # Fontes
    path('sources/', views.sources_list, name='sources_list'),
    path('sources/<int:source_id>/', views.source_detail, name='source_detail'),
    
    # Categorias
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    
    # Alertas
    path('alerts/', views.alerts_list, name='alerts_list'),
    path('alerts/<int:alert_id>/', views.alert_detail, name='alert_detail'),
    
    # Análises
    path('analytics/', views.analytics, name='analytics'),
    
    # Configurações
    path('settings/', views.settings_view, name='settings'),
    
    # Documentação
    path('api-docs/', views.api_docs, name='api_docs'),
    
    # AJAX endpoints
    path('ajax/stats/', views.ajax_stats, name='ajax_stats'),
    path('ajax/recent-articles/', views.ajax_recent_articles, name='ajax_recent_articles'),
    path('ajax/collect-source/<int:source_id>/', views.ajax_collect_source, name='ajax_collect_source'),
    path('ajax/process-articles/', views.ajax_process_articles, name='ajax_process_articles'),
] 