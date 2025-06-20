from django.core.management.base import BaseCommand
from django.utils import timezone
import re
from core.models import Category, NewsSource
from news_collector.models import SocialMediaSource


class Command(BaseCommand):
    help = 'Importa fontes de redes sociais do arquivo sites.txt'

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
        
        self.stdout.write('Importando fontes de redes sociais...')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Arquivo {file_path} não encontrado!')
            )
            return
        
        # Parse do conteúdo
        social_sources = self.parse_social_sources(content)
        
        if dry_run:
            self.stdout.write('MODO DRY-RUN - Nenhuma fonte será salva')
        
        # Contadores
        created_count = 0
        updated_count = 0
        error_count = 0
        
        # Processa cada fonte social
        for source_data in social_sources:
            try:
                if dry_run:
                    self.stdout.write(f'DRY-RUN: {source_data["account_name"]} (@{source_data["account_id"]})')
                    continue
                
                # Cria fonte de notícias principal
                news_source, created = NewsSource.objects.get_or_create(
                    name=source_data['account_name'],
                    defaults={
                        'url': f"https://twitter.com/{source_data['account_id']}",
                        'source_type': 'social',
                        'country': source_data.get('country', ''),
                        'language': source_data.get('language', 'en-US'),
                        'collection_interval': 600,  # 10 minutos para redes sociais
                        'max_articles': 100,
                        'is_active': True
                    }
                )
                
                # Cria fonte de mídia social
                social_source, social_created = SocialMediaSource.objects.get_or_create(
                    source=news_source,
                    platform='twitter',
                    account_id=source_data['account_id'],
                    defaults={
                        'account_name': source_data['account_name'],
                        'max_posts': 100,
                        'include_retweets': False,
                        'include_replies': False,
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Criada: {source_data["account_name"]} (@{source_data["account_id"]})')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Atualizada: {source_data["account_name"]} (@{source_data["account_id"]})')
                    )
                
                # Adiciona categorias baseadas no tipo de conta
                self.add_categories_to_social_source(news_source, source_data.get('category', ''))
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Erro ao processar {source_data.get("account_name", "Unknown")}: {e}')
                )
        
        # Resumo
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMO DA IMPORTAÇÃO DE REDES SOCIAIS:')
        self.stdout.write(f'Fontes criadas: {created_count}')
        self.stdout.write(f'Fontes atualizadas: {updated_count}')
        self.stdout.write(f'Erros: {error_count}')
        self.stdout.write(f'Total processadas: {len(social_sources)}')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\nImportação de redes sociais concluída!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nDRY-RUN concluído - Nenhuma alteração foi feita')
            )

    def parse_social_sources(self, content):
        """Parse as fontes de redes sociais do arquivo"""
        social_sources = []
        current_category = None
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Pula linhas vazias e comentários
            if not line or line.startswith('#') or line.startswith('🌎') or line.startswith('='):
                continue
            
            # Detecta categorias de redes sociais
            if 'Presidentes e Chefes de Estado' in line:
                current_category = 'politics'
            elif 'Bancos Centrais' in line:
                current_category = 'finance'
            elif 'Economia Global' in line:
                current_category = 'economy'
            elif 'Tecnologia & Inovação' in line:
                current_category = 'technology'
            elif 'Organizações Internacionais' in line:
                current_category = 'international'
            elif 'Outros Líderes Globais' in line:
                current_category = 'politics'
            
            # Parse linha de handle do Twitter
            elif line.startswith('@') and '–' in line:
                try:
                    # Formato: @username – Nome/Descrição
                    parts = line.split('–', 1)
                    if len(parts) == 2:
                        handle = parts[0].strip()
                        description = parts[1].strip()
                        
                        # Remove @ do handle
                        account_id = handle.replace('@', '')
                        
                        # Extrai nome da descrição
                        account_name = self.extract_name_from_description(description)
                        
                        # Determina país baseado no nome
                        country = self.determine_country_from_name(account_name, description)
                        language = self.determine_language_from_country(country)
                        
                        source_data = {
                            'account_id': account_id,
                            'account_name': account_name,
                            'description': description,
                            'category': current_category,
                            'country': country,
                            'language': language
                        }
                        
                        social_sources.append(source_data)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Erro ao parsear linha: {line} - {e}')
                    )
        
        return social_sources

    def extract_name_from_description(self, description):
        """Extrai nome da descrição"""
        # Remove informações extras entre parênteses
        clean_desc = re.sub(r'\([^)]*\)', '', description)
        
        # Remove referências de citação
        clean_desc = re.sub(r':contentReference\[[^\]]*\]\{[^}]*\}', '', clean_desc)
        
        # Remove números de seguidores
        clean_desc = re.sub(r'\d+\s*M?\s*seguidores?', '', clean_desc)
        
        # Limpa espaços extras
        clean_desc = clean_desc.strip()
        
        # Se ainda tem vírgulas, pega a primeira parte
        if ',' in clean_desc:
            clean_desc = clean_desc.split(',')[0]
        
        return clean_desc.strip()

    def determine_country_from_name(self, name, description):
        """Determina país baseado no nome e descrição"""
        text = f"{name} {description}".lower()
        
        if any(word in text for word in ['eua', 'usa', 'united states', 'biden', 'obama', 'trump', 'yellen']):
            return 'US'
        elif any(word in text for word in ['india', 'modi', 'rbi']):
            return 'IN'
        elif any(word in text for word in ['european', 'ecb', 'lagarde', 'european central bank']):
            return 'EU'
        elif any(word in text for word in ['imf', 'world bank', 'georgieva']):
            return 'INT'  # Internacional
        elif any(word in text for word in ['musk', 'tesla', 'gates', 'microsoft']):
            return 'US'
        else:
            return 'INT'  # Internacional por padrão

    def determine_language_from_country(self, country):
        """Determina idioma baseado no país"""
        language_map = {
            'US': 'en-US',
            'IN': 'en-IN',
            'EU': 'en-GB',
            'INT': 'en-US'
        }
        return language_map.get(country, 'en-US')

    def add_categories_to_social_source(self, source, category):
        """Adiciona categorias apropriadas à fonte social"""
        category_mapping = {
            'politics': ['Política', 'Internacional'],
            'finance': ['Economia', 'Finanças'],
            'economy': ['Economia', 'Internacional'],
            'technology': ['Tecnologia', 'Inovação'],
            'international': ['Internacional', 'Política']
        }
        
        categories_to_add = category_mapping.get(category, ['Internacional'])
        
        for category_name in categories_to_add:
            try:
                category_obj = Category.objects.get(name=category_name)
                source.categories.add(category_obj)
            except Category.DoesNotExist:
                # Cria categoria se não existir
                category_obj = Category.objects.create(
                    name=category_name,
                    slug=category_name.lower().replace(' ', '-'),
                    description=f'Notícias sobre {category_name.lower()}',
                    color='#007bff'
                )
                source.categories.add(category_obj)
                self.stdout.write(f'  Categoria criada: {category_name}') 