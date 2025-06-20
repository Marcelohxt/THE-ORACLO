import asyncio
import aiohttp
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import logging
import time
import json
from urllib.parse import urljoin, urlparse
import re

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from core.models import NewsSource, Article, Category, CollectionLog
from news_collector.models import ScrapingConfig, RSSFeed, SocialMediaSource

logger = logging.getLogger(__name__)


class BaseCollector:
    """Classe base para todos os coletores"""
    
    def __init__(self, source: NewsSource):
        self.source = source
        self.config = getattr(source, 'scraping_config', None)
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_collection(self, status: str, articles_collected: int = 0, errors: List[str] = None):
        """Registra log da coleta"""
        CollectionLog.objects.create(
            source=self.source,
            status=status,
            articles_collected=articles_collected,
            errors=errors or [],
            completed_at=timezone.now()
        )
    
    def clean_text(self, text: str) -> str:
        """Limpa texto removendo caracteres especiais"""
        if not text:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Remove caracteres especiais
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_date(self, date_str: str, date_format: str = None) -> Optional[datetime]:
        """Extrai data de string"""
        if not date_str:
            return None
        
        try:
            if date_format:
                return datetime.strptime(date_str, date_format)
            else:
                # Tenta formatos comuns
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%d/%m/%Y %H:%M',
                    '%d/%m/%Y',
                    '%Y-%m-%d',
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                
                return None
        except Exception as e:
            logger.warning(f"Erro ao extrair data: {date_str} - {e}")
            return None


class WebsiteCollector(BaseCollector):
    """Coletor para websites usando web scraping"""
    
    def __init__(self, source: NewsSource):
        super().__init__(source)
        self.config = getattr(source, 'scraping_config', None)
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Coleta artigos do website"""
        articles = []
        
        try:
            async with self.session.get(self.source.url) as response:
                if response.status == 200:
                    html = await response.text()
                    articles = await self.parse_html(html)
                else:
                    logger.error(f"Erro HTTP {response.status} para {self.source.url}")
                    
        except Exception as e:
            logger.error(f"Erro ao coletar de {self.source.url}: {e}")
            self.log_collection('error', errors=[str(e)])
            return []
        
        # Salva artigos no banco
        saved_count = await self.save_articles(articles)
        self.log_collection('success', saved_count)
        
        return articles
    
    async def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML e extrai artigos"""
        articles = []
        soup = BeautifulSoup(html, 'html.parser')
        
        if not self.config:
            # Tenta extração automática
            articles = self.auto_extract_articles(soup)
        else:
            # Usa configuração específica
            articles = self.config_extract_articles(soup)
        
        return articles
    
    def auto_extract_articles(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extração automática de artigos"""
        articles = []
        
        # Procura por links de artigos
        article_links = soup.find_all('a', href=True)
        
        for link in article_links[:20]:  # Limita a 20 artigos
            href = link.get('href')
            title = link.get_text().strip()
            
            if self.is_article_link(href, title):
                article = {
                    'title': title,
                    'url': urljoin(self.source.url, href),
                    'content': '',
                    'author': '',
                    'published_date': None,
                }
                articles.append(article)
        
        return articles
    
    def config_extract_articles(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extração usando configuração específica"""
        articles = []
        
        # Encontra containers de artigos
        if self.config.title_selector:
            article_elements = soup.select(self.config.title_selector)
        else:
            # Fallback para elementos comuns
            article_elements = soup.find_all(['article', 'div'], class_=re.compile(r'article|post|news'))
        
        for element in article_elements[:self.source.max_articles]:
            article = self.extract_article_data(element)
            if article:
                articles.append(article)
        
        return articles
    
    def extract_article_data(self, element) -> Optional[Dict[str, Any]]:
        """Extrai dados de um elemento de artigo"""
        try:
            # Título
            title = ""
            if self.config and self.config.title_selector:
                title_elem = element.select_one(self.config.title_selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
            else:
                title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
            
            if not title:
                return None
            
            # URL
            url = ""
            link_elem = element.find('a', href=True)
            if link_elem:
                url = urljoin(self.source.url, link_elem['href'])
            
            if not url:
                return None
            
            # Conteúdo
            content = ""
            if self.config and self.config.content_selector:
                content_elem = element.select_one(self.config.content_selector)
                if content_elem:
                    content = self.clean_text(content_elem.get_text())
            
            # Autor
            author = ""
            if self.config and self.config.author_selector:
                author_elem = element.select_one(self.config.author_selector)
                if author_elem:
                    author = self.clean_text(author_elem.get_text())
            
            # Data
            published_date = None
            if self.config and self.config.date_selector:
                date_elem = element.select_one(self.config.date_selector)
                if date_elem:
                    date_str = self.clean_text(date_elem.get_text())
                    published_date = self.extract_date(date_str, self.config.date_format)
            
            return {
                'title': title,
                'url': url,
                'content': content,
                'author': author,
                'published_date': published_date,
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do artigo: {e}")
            return None
    
    def is_article_link(self, href: str, title: str) -> bool:
        """Verifica se o link é de um artigo"""
        if not href or not title:
            return False
        
        # Verifica se tem palavras-chave de artigo na URL
        article_keywords = ['/noticia/', '/news/', '/artigo/', '/post/', '/article/']
        if any(keyword in href.lower() for keyword in article_keywords):
            return True
        
        # Verifica se o título tem tamanho adequado
        if len(title) < 10 or len(title) > 200:
            return False
        
        # Verifica se não é um link de menu/navegação
        nav_keywords = ['home', 'sobre', 'contato', 'login', 'cadastro']
        if any(keyword in title.lower() for keyword in nav_keywords):
            return False
        
        return True


class RSSCollector(BaseCollector):
    """Coletor para feeds RSS"""
    
    def __init__(self, source: NewsSource):
        super().__init__(source)
        self.rss_feeds = source.rss_feeds.filter(is_active=True)
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Coleta artigos dos feeds RSS"""
        all_articles = []
        
        for rss_feed in self.rss_feeds:
            try:
                articles = await self.collect_from_feed(rss_feed)
                all_articles.extend(articles)
                
                # Atualiza timestamp do feed
                rss_feed.last_updated = timezone.now()
                rss_feed.save()
                
            except Exception as e:
                logger.error(f"Erro ao coletar RSS {rss_feed.feed_url}: {e}")
        
        # Salva artigos no banco
        saved_count = await self.save_articles(all_articles)
        self.log_collection('success', saved_count)
        
        return all_articles
    
    async def collect_from_feed(self, rss_feed) -> List[Dict[str, Any]]:
        """Coleta de um feed RSS específico"""
        articles = []
        
        try:
            # Usa feedparser para parsear RSS
            feed = feedparser.parse(rss_feed.feed_url)
            
            for entry in feed.entries[:self.source.max_articles]:
                article = self.parse_rss_entry(entry)
                if article:
                    articles.append(article)
            
        except Exception as e:
            logger.error(f"Erro ao processar RSS {rss_feed.feed_url}: {e}")
        
        return articles
    
    def parse_rss_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Parse uma entrada RSS"""
        try:
            title = self.clean_text(entry.get('title', ''))
            if not title:
                return None
            
            # URL
            url = entry.get('link', '')
            if not url:
                return None
            
            # Conteúdo
            content = ""
            if 'summary' in entry:
                content = self.clean_text(entry.summary)
            elif 'content' in entry:
                content = self.clean_text(entry.content[0].value)
            
            # Autor
            author = ""
            if 'author' in entry:
                author = self.clean_text(entry.author)
            
            # Data
            published_date = None
            if 'published_parsed' in entry:
                published_date = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed),
                    tz=timezone.utc
                )
            elif 'updated_parsed' in entry:
                published_date = datetime.fromtimestamp(
                    time.mktime(entry.updated_parsed),
                    tz=timezone.utc
                )
            
            return {
                'title': title,
                'url': url,
                'content': content,
                'author': author,
                'published_date': published_date,
            }
            
        except Exception as e:
            logger.error(f"Erro ao parsear entrada RSS: {e}")
            return None


class APICollector(BaseCollector):
    """Coletor para APIs"""
    
    def __init__(self, source: NewsSource):
        super().__init__(source)
        self.config = getattr(source, 'scraping_config', None)
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Coleta artigos via API"""
        articles = []
        
        if not self.config or not self.config.api_endpoint:
            logger.error(f"API endpoint não configurado para {self.source.name}")
            return []
        
        try:
            headers = self.config.api_headers or {}
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            async with self.session.get(
                self.config.api_endpoint,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = self.parse_api_response(data)
                else:
                    logger.error(f"Erro HTTP {response.status} para API {self.config.api_endpoint}")
                    
        except Exception as e:
            logger.error(f"Erro ao coletar da API {self.config.api_endpoint}: {e}")
            self.log_collection('error', errors=[str(e)])
            return []
        
        # Salva artigos no banco
        saved_count = await self.save_articles(articles)
        self.log_collection('success', saved_count)
        
        return articles
    
    def parse_api_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse resposta da API"""
        articles = []
        
        # Tenta diferentes estruturas comuns de API
        items = data.get('articles', data.get('items', data.get('results', data.get('data', []))))
        
        if not isinstance(items, list):
            logger.error("Resposta da API não contém lista de artigos")
            return []
        
        for item in items[:self.source.max_articles]:
            article = self.parse_api_item(item)
            if article:
                articles.append(article)
        
        return articles
    
    def parse_api_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse um item da API"""
        try:
            title = self.clean_text(item.get('title', item.get('headline', '')))
            if not title:
                return None
            
            url = item.get('url', item.get('link', ''))
            if not url:
                return None
            
            content = self.clean_text(item.get('content', item.get('body', item.get('summary', ''))))
            author = self.clean_text(item.get('author', item.get('byline', '')))
            
            # Data
            published_date = None
            date_str = item.get('published_date', item.get('date', item.get('timestamp')))
            if date_str:
                published_date = self.extract_date(str(date_str))
            
            return {
                'title': title,
                'url': url,
                'content': content,
                'author': author,
                'published_date': published_date,
            }
            
        except Exception as e:
            logger.error(f"Erro ao parsear item da API: {e}")
            return None


class CollectorFactory:
    """Factory para criar coletores baseado no tipo de fonte"""
    
    @staticmethod
    def create_collector(source: NewsSource):
        """Cria o coletor apropriado para a fonte"""
        if source.source_type == 'rss':
            return RSSCollector(source)
        elif source.source_type == 'api':
            return APICollector(source)
        else:
            return WebsiteCollector(source)


async def collect_from_source(source: NewsSource) -> List[Dict[str, Any]]:
    """Função principal para coletar de uma fonte"""
    collector = CollectorFactory.create_collector(source)
    
    async with collector:
        return await collector.collect()


async def save_articles(articles: List[Dict[str, Any]], source: NewsSource) -> int:
    """Salva artigos no banco de dados"""
    saved_count = 0
    
    with transaction.atomic():
        for article_data in articles:
            try:
                # Verifica se o artigo já existe
                if Article.objects.filter(url=article_data['url']).exists():
                    continue
                
                # Cria o artigo
                article = Article.objects.create(
                    title=article_data['title'],
                    content=article_data['content'],
                    url=article_data['url'],
                    source=source,
                    author=article_data.get('author', ''),
                    published_date=article_data.get('published_date'),
                )
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Erro ao salvar artigo: {e}")
    
    return saved_count 