import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import json

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from core.models import Article, Analysis, Category
from data_processor.models import (
    ProcessingPipeline, ProcessingRule, SentimentModel, 
    EntityExtractor, KeywordExtractor, QualityScore
)

logger = logging.getLogger(__name__)


class BaseProcessor:
    """Classe base para todos os processadores"""
    
    def __init__(self, pipeline: ProcessingPipeline = None):
        self.pipeline = pipeline
        self.rules = []
        if pipeline:
            self.rules = ProcessingRule.objects.filter(
                is_active=True,
                rule_type__in=pipeline.rules
            ).order_by('priority')
    
    def apply_rules(self, text: str) -> str:
        """Aplica regras de processamento ao texto"""
        processed_text = text
        
        for rule in self.rules:
            try:
                processed_text = self.apply_rule(rule, processed_text)
            except Exception as e:
                logger.error(f"Erro ao aplicar regra {rule.name}: {e}")
        
        return processed_text
    
    def apply_rule(self, rule: ProcessingRule, text: str) -> str:
        """Aplica uma regra específica"""
        rule_type = rule.rule_type
        parameters = rule.parameters
        
        if rule_type == 'text_filter':
            return self.apply_text_filter(text, parameters)
        elif rule_type == 'regex_replace':
            return self.apply_regex_replace(text, parameters)
        elif rule_type == 'html_clean':
            return self.clean_html(text)
        else:
            return text
    
    def apply_text_filter(self, text: str, parameters: Dict) -> str:
        """Aplica filtro de texto"""
        # Remove palavras específicas
        if 'remove_words' in parameters:
            words = parameters['remove_words']
            for word in words:
                text = re.sub(rf'\b{re.escape(word)}\b', '', text, flags=re.IGNORECASE)
        
        # Remove padrões
        if 'remove_patterns' in parameters:
            patterns = parameters['remove_patterns']
            for pattern in patterns:
                text = re.sub(pattern, '', text)
        
        return text
    
    def apply_regex_replace(self, text: str, parameters: Dict) -> str:
        """Aplica substituição regex"""
        if 'pattern' in parameters and 'replacement' in parameters:
            pattern = parameters['pattern']
            replacement = parameters['replacement']
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def clean_html(self, text: str) -> str:
        """Remove HTML do texto"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()


class SentimentProcessor(BaseProcessor):
    """Processador de análise de sentimento"""
    
    def __init__(self, model: SentimentModel = None):
        super().__init__()
        self.model = model or SentimentModel.objects.filter(is_default=True, is_active=True).first()
        self._vader_analyzer = None
        self._textblob = None
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analisa sentimento do texto"""
        if not text:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}
        
        if not self.model:
            return self._fallback_sentiment(text)
        
        start_time = timezone.now()
        
        try:
            if self.model.model_type == 'vader':
                result = self._analyze_vader(text)
            elif self.model.model_type == 'textblob':
                result = self._analyze_textblob(text)
            else:
                result = self._fallback_sentiment(text)
            
            # Calcula tempo de processamento
            processing_time = (timezone.now() - start_time).total_seconds()
            
            # Atualiza estatísticas do modelo
            self.model.total_processed += 1
            if self.model.avg_processing_time:
                self.model.avg_processing_time = (
                    (self.model.avg_processing_time + processing_time) / 2
                )
            else:
                self.model.avg_processing_time = processing_time
            self.model.save()
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            return self._fallback_sentiment(text)
    
    def _analyze_vader(self, text: str) -> Dict[str, Any]:
        """Análise usando VADER"""
        if not self._vader_analyzer:
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self._vader_analyzer = SentimentIntensityAnalyzer()
            except ImportError:
                logger.error("VADER não disponível")
                return self._fallback_sentiment(text)
        
        scores = self._vader_analyzer.polarity_scores(text)
        
        # Determina label baseado no compound score
        compound = scores['compound']
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': compound,
            'label': label,
            'confidence': abs(compound),
            'details': scores
        }
    
    def _analyze_textblob(self, text: str) -> Dict[str, Any]:
        """Análise usando TextBlob"""
        if not self._textblob:
            try:
                from textblob import TextBlob
                self._textblob = TextBlob
            except ImportError:
                logger.error("TextBlob não disponível")
                return self._fallback_sentiment(text)
        
        blob = self._textblob(text)
        polarity = blob.sentiment.polarity
        
        # Determina label
        if polarity > 0:
            label = 'positive'
        elif polarity < 0:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': polarity,
            'label': label,
            'confidence': abs(polarity),
            'details': {
                'polarity': polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
        }
    
    def _fallback_sentiment(self, text: str) -> Dict[str, Any]:
        """Análise de sentimento básica como fallback"""
        # Palavras positivas e negativas em português
        positive_words = [
            'bom', 'ótimo', 'excelente', 'fantástico', 'maravilhoso', 'incrível',
            'positivo', 'sucesso', 'crescimento', 'lucro', 'ganho', 'vitória'
        ]
        
        negative_words = [
            'ruim', 'terrível', 'horrível', 'péssimo', 'negativo', 'fracasso',
            'perda', 'queda', 'crise', 'problema', 'erro', 'falha'
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            score = 0.3
            label = 'positive'
        elif negative_count > positive_count:
            score = -0.3
            label = 'negative'
        else:
            score = 0.0
            label = 'neutral'
        
        return {
            'score': score,
            'label': label,
            'confidence': 0.5,
            'details': {
                'positive_words': positive_count,
                'negative_words': negative_count
            }
        }


class EntityProcessor(BaseProcessor):
    """Processador de extração de entidades"""
    
    def __init__(self, extractor: EntityExtractor = None):
        super().__init__()
        self.extractor = extractor or EntityExtractor.objects.filter(is_default=True, is_active=True).first()
        self._spacy_model = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extrai entidades nomeadas do texto"""
        if not text:
            return []
        
        if not self.extractor:
            return self._fallback_entities(text)
        
        start_time = timezone.now()
        
        try:
            if self.extractor.extractor_type == 'spacy':
                entities = self._extract_spacy_entities(text)
            elif self.extractor.extractor_type == 'regex':
                entities = self._extract_regex_entities(text)
            else:
                entities = self._fallback_entities(text)
            
            # Filtra entidades por tipo se especificado
            if self.extractor.entity_types:
                entities = [
                    entity for entity in entities 
                    if entity['type'] in self.extractor.entity_types
                ]
            
            # Atualiza estatísticas
            processing_time = (timezone.now() - start_time).total_seconds()
            self.extractor.total_processed += 1
            if self.extractor.avg_processing_time:
                self.extractor.avg_processing_time = (
                    (self.extractor.avg_processing_time + processing_time) / 2
                )
            else:
                self.extractor.avg_processing_time = processing_time
            self.extractor.save()
            
            return entities
            
        except Exception as e:
            logger.error(f"Erro na extração de entidades: {e}")
            return self._fallback_entities(text)
    
    def _extract_spacy_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extração usando spaCy"""
        if not self._spacy_model:
            try:
                import spacy
                # Tenta carregar modelo português, senão inglês
                try:
                    self._spacy_model = spacy.load('pt_core_news_sm')
                except:
                    self._spacy_model = spacy.load('en_core_web_sm')
            except ImportError:
                logger.error("spaCy não disponível")
                return self._fallback_entities(text)
        
        doc = self._spacy_model(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 0.8  # spaCy não fornece confiança
            })
        
        return entities
    
    def _extract_regex_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extração usando regex"""
        entities = []
        parameters = self.extractor.parameters
        
        # Padrões regex para diferentes tipos de entidades
        patterns = parameters.get('patterns', {
            'PERSON': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'ORG': r'\b[A-Z][A-Z\s&]+(?:Corp|Inc|Ltd|LLC|SA|LTDA)\b',
            'LOC': r'\b[A-Z][a-z]+(?: de | da | do )?[A-Z][a-z]+\b',
        })
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'type': entity_type,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.6
                })
        
        return entities
    
    def _fallback_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extração básica de entidades como fallback"""
        entities = []
        
        # Procura por nomes próprios (palavras com inicial maiúscula)
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                # Verifica se é seguido por outro nome próprio (nome completo)
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    full_name = f"{word} {words[i + 1]}"
                    entities.append({
                        'text': full_name,
                        'type': 'PERSON',
                        'start': text.find(full_name),
                        'end': text.find(full_name) + len(full_name),
                        'confidence': 0.5
                    })
        
        return entities


class KeywordProcessor(BaseProcessor):
    """Processador de extração de palavras-chave"""
    
    def __init__(self, extractor: KeywordExtractor = None):
        super().__init__()
        self.extractor = extractor or KeywordExtractor.objects.filter(is_default=True, is_active=True).first()
    
    def extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extrai palavras-chave do texto"""
        if not text:
            return []
        
        if not self.extractor:
            return self._fallback_keywords(text)
        
        start_time = timezone.now()
        
        try:
            if self.extractor.extractor_type == 'tfidf':
                keywords = self._extract_tfidf_keywords(text)
            elif self.extractor.extractor_type == 'yake':
                keywords = self._extract_yake_keywords(text)
            else:
                keywords = self._fallback_keywords(text)
            
            # Filtra por tamanho mínimo
            keywords = [
                kw for kw in keywords 
                if len(kw['text']) >= self.extractor.min_keyword_length
            ]
            
            # Remove stop words
            if self.extractor.stop_words:
                keywords = [
                    kw for kw in keywords 
                    if kw['text'].lower() not in self.extractor.stop_words
                ]
            
            # Limita número de keywords
            keywords = keywords[:self.extractor.max_keywords]
            
            # Atualiza estatísticas
            processing_time = (timezone.now() - start_time).total_seconds()
            self.extractor.total_processed += 1
            if self.extractor.avg_processing_time:
                self.extractor.avg_processing_time = (
                    (self.extractor.avg_processing_time + processing_time) / 2
                )
            else:
                self.extractor.avg_processing_time = processing_time
            self.extractor.save()
            
            return keywords
            
        except Exception as e:
            logger.error(f"Erro na extração de keywords: {e}")
            return self._fallback_keywords(text)
    
    def _extract_tfidf_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extração usando TF-IDF"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.feature_extraction.text import CountVectorizer
            
            # Tokeniza o texto
            vectorizer = CountVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Calcula TF-IDF
            tfidf = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = tfidf.fit_transform([text])
            feature_names = tfidf.get_feature_names_out()
            
            # Obtém scores
            scores = tfidf_matrix.toarray()[0]
            
            # Cria lista de keywords
            keywords = []
            for i, score in enumerate(scores):
                if score > 0:
                    keywords.append({
                        'text': feature_names[i],
                        'score': float(score),
                        'type': 'tfidf'
                    })
            
            # Ordena por score
            keywords.sort(key=lambda x: x['score'], reverse=True)
            
            return keywords
            
        except ImportError:
            logger.error("scikit-learn não disponível")
            return self._fallback_keywords(text)
    
    def _extract_yake_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extração usando YAKE"""
        try:
            import yake
            
            # Configura YAKE
            kw_extractor = yake.KeywordExtractor(
                lan="pt",
                n=1,
                dedupLim=0.3,
                top=20
            )
            
            keywords = kw_extractor.extract_keywords(text)
            
            # Converte para formato padrão
            result = []
            for keyword, score in keywords:
                result.append({
                    'text': keyword,
                    'score': 1.0 - score,  # YAKE retorna scores menores = melhor
                    'type': 'yake'
                })
            
            return result
            
        except ImportError:
            logger.error("YAKE não disponível")
            return self._fallback_keywords(text)
    
    def _fallback_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Extração básica de keywords como fallback"""
        # Remove pontuação e converte para minúsculas
        text_clean = re.sub(r'[^\w\s]', '', text.lower())
        words = text_clean.split()
        
        # Conta frequência das palavras
        word_freq = {}
        for word in words:
            if len(word) >= 3:  # Palavras com pelo menos 3 caracteres
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Converte para lista de keywords
        keywords = []
        for word, freq in word_freq.items():
            if freq > 1:  # Palavras que aparecem mais de uma vez
                keywords.append({
                    'text': word,
                    'score': freq / len(words),  # Frequência normalizada
                    'type': 'frequency'
                })
        
        # Ordena por score
        keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return keywords


class QualityProcessor(BaseProcessor):
    """Processador de qualidade de conteúdo"""
    
    def calculate_quality_score(self, article: Article) -> Dict[str, Any]:
        """Calcula score de qualidade do artigo"""
        scores = {}
        
        # Score de legibilidade
        scores['readability'] = self._calculate_readability(article.content)
        
        # Score de completude
        scores['completeness'] = self._calculate_completeness(article)
        
        # Score de precisão (baseado em fatores como presença de datas, nomes, etc.)
        scores['accuracy'] = self._calculate_accuracy(article)
        
        # Score de relevância (baseado em keywords e entidades)
        scores['relevance'] = self._calculate_relevance(article)
        
        # Score geral (média ponderada)
        weights = {
            'readability': 0.2,
            'completeness': 0.3,
            'accuracy': 0.25,
            'relevance': 0.25
        }
        
        overall_score = sum(
            scores[key] * weights[key] 
            for key in scores.keys()
        )
        
        return {
            'overall_score': overall_score,
            'scores': scores,
            'factors': self._get_quality_factors(article, scores)
        }
    
    def _calculate_readability(self, text: str) -> float:
        """Calcula score de legibilidade"""
        if not text:
            return 0.0
        
        # Fórmula de Flesch-Kincaid adaptada para português
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        syllables = self._count_syllables(text)
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Fórmula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        readability = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        
        # Normaliza para 0-1
        return max(0.0, min(1.0, readability / 100.0))
    
    def _count_syllables(self, text: str) -> int:
        """Conta sílabas no texto (aproximação)"""
        # Regra simples: cada vogal é uma sílaba
        vowels = 'aeiouáéíóúâêîôûãõ'
        count = 0
        for char in text.lower():
            if char in vowels:
                count += 1
        return count
    
    def _calculate_completeness(self, article: Article) -> float:
        """Calcula score de completude"""
        factors = []
        
        # Título
        if article.title and len(article.title) > 10:
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        # Conteúdo
        if article.content and len(article.content) > 100:
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        # Autor
        if article.author:
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        # Data de publicação
        if article.published_date:
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        # URL
        if article.url:
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        return sum(factors) / len(factors)
    
    def _calculate_accuracy(self, article: Article) -> float:
        """Calcula score de precisão"""
        factors = []
        
        # Presença de datas
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', article.content):
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        # Presença de números
        if re.search(r'\d+', article.content):
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        # Presença de nomes próprios
        if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', article.content):
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        # Presença de citações
        if '"' in article.content or '"' in article.content:
            factors.append(1.0)
        else:
            factors.append(0.0)
        
        return sum(factors) / len(factors) if factors else 0.0
    
    def _calculate_relevance(self, article: Article) -> float:
        """Calcula score de relevância"""
        # Baseado em keywords e entidades extraídas
        relevance_factors = []
        
        if article.keywords:
            relevance_factors.append(min(1.0, len(article.keywords) / 10.0))
        else:
            relevance_factors.append(0.0)
        
        if article.entities:
            relevance_factors.append(min(1.0, len(article.entities) / 5.0))
        else:
            relevance_factors.append(0.0)
        
        return sum(relevance_factors) / len(relevance_factors) if relevance_factors else 0.0
    
    def _get_quality_factors(self, article: Article, scores: Dict[str, float]) -> Dict[str, Any]:
        """Obtém fatores que influenciam a qualidade"""
        factors = {
            'has_title': bool(article.title),
            'has_content': bool(article.content),
            'has_author': bool(article.author),
            'has_date': bool(article.published_date),
            'content_length': len(article.content) if article.content else 0,
            'title_length': len(article.title) if article.title else 0,
            'has_keywords': bool(article.keywords),
            'has_entities': bool(article.entities),
            'keyword_count': len(article.keywords) if article.keywords else 0,
            'entity_count': len(article.entities) if article.entities else 0,
        }
        
        return factors


class ProcessingManager:
    """Gerenciador de processamento"""
    
    def __init__(self):
        self.sentiment_processor = SentimentProcessor()
        self.entity_processor = EntityProcessor()
        self.keyword_processor = KeywordProcessor()
        self.quality_processor = QualityProcessor()
    
    async def process_article(self, article: Article) -> Dict[str, Any]:
        """Processa um artigo completo"""
        results = {}
        
        try:
            # Análise de sentimento
            sentiment_result = self.sentiment_processor.analyze_sentiment(article.content)
            results['sentiment'] = sentiment_result
            
            # Extração de entidades
            entities = self.entity_processor.extract_entities(article.content)
            results['entities'] = entities
            
            # Extração de keywords
            keywords = self.keyword_processor.extract_keywords(article.content)
            results['keywords'] = keywords
            
            # Score de qualidade
            quality_result = self.quality_processor.calculate_quality_score(article)
            results['quality'] = quality_result
            
            # Salva resultados no banco
            await self._save_analysis_results(article, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao processar artigo {article.id}: {e}")
            return {}
    
    async def _save_analysis_results(self, article: Article, results: Dict[str, Any]):
        """Salva resultados da análise no banco"""
        with transaction.atomic():
            # Atualiza artigo
            if 'sentiment' in results:
                article.sentiment_score = results['sentiment']['score']
            
            if 'keywords' in results:
                article.keywords = [kw['text'] for kw in results['keywords']]
            
            if 'entities' in results:
                article.entities = results['entities']
            
            if 'quality' in results:
                article.relevance_score = results['quality']['overall_score']
            
            article.status = 'analyzed'
            article.save()
            
            # Salva análises individuais
            for analysis_type, result in results.items():
                Analysis.objects.update_or_create(
                    article=article,
                    analysis_type=analysis_type,
                    defaults={
                        'result': result,
                        'confidence': result.get('confidence', 0.0),
                        'processing_time': result.get('processing_time', 0.0)
                    }
                )
            
            # Salva score de qualidade
            if 'quality' in results:
                QualityScore.objects.update_or_create(
                    article=article,
                    defaults={
                        'readability_score': results['quality']['scores']['readability'],
                        'completeness_score': results['quality']['scores']['completeness'],
                        'accuracy_score': results['quality']['scores']['accuracy'],
                        'relevance_score': results['quality']['scores']['relevance'],
                        'overall_score': results['quality']['overall_score'],
                        'factors': results['quality']['factors']
                    }
                )
    
    async def process_batch(self, articles: List[Article]) -> Dict[str, Any]:
        """Processa um lote de artigos"""
        results = {
            'total': len(articles),
            'processed': 0,
            'errors': 0,
            'processing_time': 0.0
        }
        
        start_time = timezone.now()
        
        for article in articles:
            try:
                await self.process_article(article)
                results['processed'] += 1
            except Exception as e:
                logger.error(f"Erro ao processar artigo {article.id}: {e}")
                results['errors'] += 1
        
        results['processing_time'] = (timezone.now() - start_time).total_seconds()
        
        return results 