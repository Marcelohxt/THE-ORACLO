from django.core.management.base import BaseCommand
from django.utils import timezone
import re
from core.models import Category, NewsSource
from news_collector.models import ScrapingConfig


class Command(BaseCommand):
    help = 'Importa fontes de notícias do arquivo sites.txt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='sites.txt',
            help='Caminho para o arquivo sites.txt'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar no banco de dados'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        self.stdout.write('Importando fontes de notícias...')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Arquivo {file_path} não encontrado!')
            )
            return
        
        # Parse do conteúdo
        sources = self.parse_sources(content)
        
        if dry_run:
            self.stdout.write('MODO DRY-RUN - Nenhuma fonte será salva')
        
        # Contadores
        created_count = 0
        updated_count = 0
        error_count = 0
        
        # Processa cada fonte
        for source_data in sources:
            try:
                if dry_run:
                    self.stdout.write(f'DRY-RUN: {source_data["name"]} - {source_data["url"]}')
                    continue
                
                # Cria ou atualiza a fonte
                source, created = NewsSource.objects.get_or_create(
                    url=source_data['url'],
                    defaults=source_data
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Criada: {source.name}')
                    )
                else:
                    # Atualiza dados existentes
                    for key, value in source_data.items():
                        if key != 'url':  # Não atualiza a URL
                            setattr(source, key, value)
                    source.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Atualizada: {source.name}')
                    )
                
                # Adiciona categorias baseadas no país/região
                self.add_categories_to_source(source, source_data.get('country', ''))
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Erro ao processar {source_data.get("name", "Unknown")}: {e}')
                )
        
        # Resumo
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMO DA IMPORTAÇÃO:')
        self.stdout.write(f'Fontes criadas: {created_count}')
        self.stdout.write(f'Fontes atualizadas: {updated_count}')
        self.stdout.write(f'Erros: {error_count}')
        self.stdout.write(f'Total processadas: {len(sources)}')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\nImportação concluída com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nDRY-RUN concluído - Nenhuma alteração foi feita')
            )

    def parse_sources(self, content):
        """Parse o conteúdo do arquivo sites.txt"""
        sources = []
        current_country = None
        current_language = 'pt-BR'  # Default
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Pula linhas vazias e comentários
            if not line or line.startswith('#') or line.startswith('🌎') or line.startswith('='):
                continue
            
            # Detecta país/região
            if line.startswith('🇧🇷'):
                current_country = 'BR'
                current_language = 'pt-BR'
            elif line.startswith('🇺🇸'):
                current_country = 'US'
                current_language = 'en-US'
            elif line.startswith('🇬🇧'):
                current_country = 'GB'
                current_language = 'en-GB'
            elif line.startswith('🇫🇷'):
                current_country = 'FR'
                current_language = 'fr-FR'
            elif line.startswith('🇩🇪'):
                current_country = 'DE'
                current_language = 'de-DE'
            elif line.startswith('🇪🇸'):
                current_country = 'ES'
                current_language = 'es-ES'
            elif line.startswith('🇯🇵'):
                current_country = 'JP'
                current_language = 'ja-JP'
            elif line.startswith('🇨🇳'):
                current_country = 'CN'
                current_language = 'zh-CN'
            elif line.startswith('🇮🇳'):
                current_country = 'IN'
                current_language = 'en-IN'
            elif line.startswith('🇦🇷'):
                current_country = 'AR'
                current_language = 'es-AR'
            elif line.startswith('🇲🇽'):
                current_country = 'MX'
                current_language = 'es-MX'
            elif line.startswith('🌎'):
                current_country = 'LA'
                current_language = 'es-ES'
            
            # Parse linha de fonte
            elif ' - ' in line and 'http' in line:
                try:
                    # Remove emojis e formatação
                    clean_line = re.sub(r'[🇧🇷🇺🇸🇬🇧🇫🇷🇩🇪🇪🇸🇯🇵🇨🇳🇮🇳🇦🇷🇲🇽🌎]', '', line).strip()
                    
                    if ' - ' in clean_line:
                        name, url = clean_line.split(' - ', 1)
                        name = name.strip()
                        url = url.strip()
                        
                        # Valida URL
                        if not url.startswith('http'):
                            continue
                        
                        # Determina tipo de fonte
                        source_type = self.determine_source_type(url)
                        
                        source_data = {
                            'name': name,
                            'url': url,
                            'source_type': source_type,
                            'country': current_country,
                            'language': current_language,
                            'collection_interval': 300,  # 5 minutos
                            'max_articles': 50,
                            'is_active': True
                        }
                        
                        sources.append(source_data)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Erro ao parsear linha: {line} - {e}')
                    )
        
        return sources

    def determine_source_type(self, url):
        """Determina o tipo de fonte baseado na URL"""
        url_lower = url.lower()
        
        if 'rss' in url_lower or 'feed' in url_lower:
            return 'rss'
        elif 'api' in url_lower:
            return 'api'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'social'
        elif 'telegram' in url_lower:
            return 'telegram'
        else:
            return 'website'

    def add_categories_to_source(self, source, country):
        """Adiciona categorias apropriadas à fonte baseado no país"""
        # Categorias padrão para todas as fontes
        default_categories = ['Política', 'Economia', 'Internacional']
        
        # Categorias específicas por país
        country_categories = {
            'BR': ['Política', 'Economia', 'Tecnologia', 'Saúde', 'Educação', 'Esportes'],
            'US': ['Política', 'Economia', 'Tecnologia', 'Internacional', 'Segurança'],
            'GB': ['Política', 'Economia', 'Internacional', 'Tecnologia'],
            'FR': ['Política', 'Economia', 'Internacional', 'Cultura'],
            'DE': ['Política', 'Economia', 'Tecnologia', 'Internacional'],
            'ES': ['Política', 'Economia', 'Internacional', 'Cultura'],
            'JP': ['Tecnologia', 'Economia', 'Internacional'],
            'CN': ['Economia', 'Tecnologia', 'Internacional'],
            'IN': ['Política', 'Economia', 'Tecnologia', 'Internacional'],
            'AR': ['Política', 'Economia', 'Internacional'],
            'MX': ['Política', 'Economia', 'Internacional'],
        }
        
        # Seleciona categorias baseado no país
        categories_to_add = country_categories.get(country, default_categories)
        
        # Adiciona categorias à fonte
        for category_name in categories_to_add:
            try:
                category = Category.objects.get(name=category_name)
                source.categories.add(category)
            except Category.DoesNotExist:
                # Cria categoria se não existir
                category = Category.objects.create(
                    name=category_name,
                    slug=category_name.lower().replace(' ', '-'),
                    description=f'Notícias sobre {category_name.lower()}',
                    color='#007bff'
                )
                source.categories.add(category)
                self.stdout.write(f'  Categoria criada: {category_name}')

    def create_scraping_configs(self):
        """Cria configurações de scraping básicas para fontes conhecidas"""
        configs = {
            'G1': {
                'title_selector': 'h1, h2, h3',
                'content_selector': '.content-text__container',
                'author_selector': '.content-publication-data__from',
                'date_selector': '.content-publication-data__updated',
            },
            'UOL Notícias': {
                'title_selector': 'h1, h2',
                'content_selector': '.text',
                'author_selector': '.author',
                'date_selector': '.date',
            },
            'CNN Brasil': {
                'title_selector': 'h1, h2',
                'content_selector': '.content-text',
                'author_selector': '.author-name',
                'date_selector': '.published-date',
            },
            'Folha de S.Paulo': {
                'title_selector': 'h1, h2',
                'content_selector': '.content-text',
                'author_selector': '.author',
                'date_selector': '.published-date',
            },
            'Estadão': {
                'title_selector': 'h1, h2',
                'content_selector': '.content-text',
                'author_selector': '.author',
                'date_selector': '.published-date',
            },
            'CNN': {
                'title_selector': 'h1, h2',
                'content_selector': '.zn-body__paragraph',
                'author_selector': '.metadata__byline',
                'date_selector': '.metadata__date',
            },
            'BBC News': {
                'title_selector': 'h1, h2',
                'content_selector': '.gs-c-promo-summary',
                'author_selector': '.gs-c-promo-meta',
                'date_selector': '.gs-c-promo-meta',
            },
        }
        
        for source_name, config in configs.items():
            try:
                source = NewsSource.objects.get(name=source_name)
                ScrapingConfig.objects.get_or_create(
                    source=source,
                    defaults=config
                )
                self.stdout.write(f'  Config de scraping criada: {source_name}')
            except NewsSource.DoesNotExist:
                pass 