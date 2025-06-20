#!/usr/bin/env python
"""
Script de teste para o ORACLO
Verifica se todas as dependências e configurações estão funcionando
"""

import os
import sys
import django
from pathlib import Path

# Adiciona o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oraclo.settings')
django.setup()

def test_django_setup():
    """Testa se o Django está configurado corretamente"""
    print("🔧 Testando configuração do Django...")
    
    try:
        from django.conf import settings
        print(f"✓ Django configurado - DEBUG: {settings.DEBUG}")
        print(f"✓ Banco de dados: {settings.DATABASES['default']['ENGINE']}")
        return True
    except Exception as e:
        print(f"✗ Erro na configuração do Django: {e}")
        return False

def test_models():
    """Testa se os modelos estão funcionando"""
    print("\n📊 Testando modelos...")
    
    try:
        from core.models import Category, NewsSource, Article
        from news_collector.models import ScrapingConfig
        from data_processor.models import ProcessingPipeline
        
        print("✓ Modelos importados com sucesso")
        
        # Testa criação de objetos
        category_count = Category.objects.count()
        source_count = NewsSource.objects.count()
        article_count = Article.objects.count()
        
        print(f"✓ Categorias no banco: {category_count}")
        print(f"✓ Fontes no banco: {source_count}")
        print(f"✓ Artigos no banco: {article_count}")
        
        return True
    except Exception as e:
        print(f"✗ Erro nos modelos: {e}")
        return False

def test_collectors():
    """Testa se os coletores estão funcionando"""
    print("\n🌐 Testando coletores...")
    
    try:
        from news_collector.collectors import BaseCollector, WebsiteCollector, RSSCollector
        
        print("✓ Coletores importados com sucesso")
        
        # Testa criação de coletor
        from core.models import NewsSource
        sources = NewsSource.objects.filter(is_active=True)[:1]
        
        if sources.exists():
            source = sources.first()
            collector = WebsiteCollector(source)
            print(f"✓ Coletor criado para: {source.name}")
        else:
            print("⚠ Nenhuma fonte ativa encontrada para teste")
        
        return True
    except Exception as e:
        print(f"✗ Erro nos coletores: {e}")
        return False

def test_processors():
    """Testa se os processadores estão funcionando"""
    print("\n🧠 Testando processadores...")
    
    try:
        from data_processor.processors import (
            BaseProcessor, SentimentProcessor, 
            EntityProcessor, KeywordProcessor
        )
        
        print("✓ Processadores importados com sucesso")
        
        # Testa processador de sentimento
        processor = SentimentProcessor()
        test_text = "Este é um texto de teste muito positivo e otimista!"
        result = processor.analyze_sentiment(test_text)
        
        print(f"✓ Análise de sentimento funcionando - Score: {result.get('score', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"✗ Erro nos processadores: {e}")
        return False

def test_api():
    """Testa se a API está funcionando"""
    print("\n🔌 Testando API...")
    
    try:
        from core.serializers import (
            ArticleSerializer, NewsSourceSerializer, 
            CategorySerializer
        )
        
        print("✓ Serializers importados com sucesso")
        
        # Testa serialização
        from core.models import Category
        categories = Category.objects.all()[:1]
        
        if categories.exists():
            serializer = CategorySerializer(categories.first())
            print("✓ Serialização funcionando")
        else:
            print("⚠ Nenhuma categoria encontrada para teste")
        
        return True
    except Exception as e:
        print(f"✗ Erro na API: {e}")
        return False

def test_admin():
    """Testa se o admin está configurado"""
    print("\n⚙️ Testando admin...")
    
    try:
        from django.contrib import admin
        from core.admin import CategoryAdmin, NewsSourceAdmin, ArticleAdmin
        
        print("✓ Admin configurado com sucesso")
        
        # Verifica se os modelos estão registrados
        registered_models = [model.__name__ for model in admin.site._registry.keys()]
        expected_models = ['Category', 'NewsSource', 'Article', 'Analysis', 'Alert']
        
        for model in expected_models:
            if model in registered_models:
                print(f"✓ {model} registrado no admin")
            else:
                print(f"⚠ {model} não encontrado no admin")
        
        return True
    except Exception as e:
        print(f"✗ Erro no admin: {e}")
        return False

def test_dependencies():
    """Testa se as dependências estão instaladas"""
    print("\n📦 Testando dependências...")
    
    dependencies = [
        ('requests', 'requests'),
        ('aiohttp', 'aiohttp'),
        ('beautifulsoup4', 'bs4'),
        ('feedparser', 'feedparser'),
        ('nltk', 'nltk'),
        ('spacy', 'spacy'),
        ('sklearn', 'sklearn'),
        ('vaderSentiment', 'vaderSentiment'),
        ('redis', 'redis'),
    ]
    
    all_ok = True
    
    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - NÃO INSTALADO")
            all_ok = False
    
    return all_ok

def test_database_connection():
    """Testa conexão com banco de dados"""
    print("\n🗄️ Testando conexão com banco...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        if result and result[0] == 1:
            print("✓ Conexão com banco de dados OK")
            return True
        else:
            print("✗ Erro na conexão com banco")
            return False
    except Exception as e:
        print(f"✗ Erro na conexão com banco: {e}")
        return False

def test_redis_connection():
    """Testa conexão com Redis"""
    print("\n🔴 Testando conexão com Redis...")
    
    try:
        import redis
        from django.conf import settings
        
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
        
        # Testa ping
        response = r.ping()
        if response:
            print("✓ Conexão com Redis OK")
            return True
        else:
            print("✗ Redis não respondeu ao ping")
            return False
    except Exception as e:
        print(f"✗ Erro na conexão com Redis: {e}")
        print("⚠ Redis não está rodando ou não configurado")
        return False

def main():
    """Função principal de teste"""
    print("🚀 TESTE DO ORACLO")
    print("=" * 50)
    
    tests = [
        ("Django Setup", test_django_setup),
        ("Dependências", test_dependencies),
        ("Conexão com Banco", test_database_connection),
        ("Conexão com Redis", test_redis_connection),
        ("Modelos", test_models),
        ("Coletores", test_collectors),
        ("Processadores", test_processors),
        ("API", test_api),
        ("Admin", test_admin),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 ORACLO está funcionando perfeitamente!")
        print("\nPróximos passos:")
        print("1. Execute: python manage.py init_oraclo")
        print("2. Execute: python manage.py import_sources")
        print("3. Acesse: http://localhost:8000/admin/")
        print("4. Acesse: http://localhost:8000/dashboard/")
    else:
        print("⚠ Alguns testes falharam. Verifique as dependências e configurações.")
        print("\nComandos úteis:")
        print("- pip install -r requirements.txt")
        print("- python manage.py migrate")
        print("- python manage.py collectstatic")

if __name__ == "__main__":
    main() 