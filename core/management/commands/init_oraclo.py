from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Category, NewsSource
from news_collector.models import ScrapingConfig


class Command(BaseCommand):
    help = 'Inicializa o ORACLO com dados básicos'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando ORACLO...')
        
        # Cria categorias básicas
        categories_data = [
            {
                'name': 'Política',
                'slug': 'politica',
                'description': 'Notícias sobre política nacional e internacional',
                'color': '#dc3545'
            },
            {
                'name': 'Economia',
                'slug': 'economia',
                'description': 'Notícias sobre economia, finanças e mercado',
                'color': '#28a745'
            },
            {
                'name': 'Tecnologia',
                'slug': 'tecnologia',
                'description': 'Notícias sobre tecnologia e inovação',
                'color': '#007bff'
            },
            {
                'name': 'Saúde',
                'slug': 'saude',
                'description': 'Notícias sobre saúde e bem-estar',
                'color': '#17a2b8'
            },
            {
                'name': 'Educação',
                'slug': 'educacao',
                'description': 'Notícias sobre educação e ensino',
                'color': '#ffc107'
            },
            {
                'name': 'Esportes',
                'slug': 'esportes',
                'description': 'Notícias sobre esportes e competições',
                'color': '#fd7e14'
            },
            {
                'name': 'Entretenimento',
                'slug': 'entretenimento',
                'description': 'Notícias sobre entretenimento e cultura',
                'color': '#e83e8c'
            },
            {
                'name': 'Internacional',
                'slug': 'internacional',
                'description': 'Notícias internacionais',
                'color': '#6f42c1'
            },
            {
                'name': 'Segurança',
                'slug': 'seguranca',
                'description': 'Notícias sobre segurança e defesa',
                'color': '#343a40'
            },
            {
                'name': 'Meio Ambiente',
                'slug': 'meio-ambiente',
                'description': 'Notícias sobre meio ambiente e sustentabilidade',
                'color': '#20c997'
            }
        ]
        
        categories_created = 0
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                categories_created += 1
                self.stdout.write(f'Categoria criada: {category.name}')
        
        self.stdout.write(f'{categories_created} categorias criadas')
        
        # Cria fontes de notícias básicas
        sources_data = [
            {
                'name': 'G1',
                'url': 'https://g1.globo.com',
                'source_type': 'website',
                'country': 'BR',
                'language': 'pt-BR',
                'collection_interval': 300,
                'max_articles': 50
            },
            {
                'name': 'UOL Notícias',
                'url': 'https://noticias.uol.com.br',
                'source_type': 'website',
                'country': 'BR',
                'language': 'pt-BR',
                'collection_interval': 300,
                'max_articles': 50
            },
            {
                'name': 'CNN Brasil',
                'url': 'https://www.cnnbrasil.com.br',
                'source_type': 'website',
                'country': 'BR',
                'language': 'pt-BR',
                'collection_interval': 300,
                'max_articles': 50
            },
            {
                'name': 'Folha de S.Paulo',
                'url': 'https://www.folha.uol.com.br',
                'source_type': 'website',
                'country': 'BR',
                'language': 'pt-BR',
                'collection_interval': 300,
                'max_articles': 50
            },
            {
                'name': 'Estadão',
                'url': 'https://www.estadao.com.br',
                'source_type': 'website',
                'country': 'BR',
                'language': 'pt-BR',
                'collection_interval': 300,
                'max_articles': 50
            }
        ]
        
        sources_created = 0
        for source_data in sources_data:
            source, created = NewsSource.objects.get_or_create(
                url=source_data['url'],
                defaults=source_data
            )
            if created:
                sources_created += 1
                self.stdout.write(f'Fonte criada: {source.name}')
                
                # Adiciona categorias padrão
                politica = Category.objects.get(slug='politica')
                economia = Category.objects.get(slug='economia')
                source.categories.add(politica, economia)
        
        self.stdout.write(f'{sources_created} fontes criadas')
        
        # Cria configurações de scraping básicas
        scraping_configs = [
            {
                'source_name': 'G1',
                'title_selector': 'h1, h2, h3',
                'content_selector': '.content-text__container',
                'author_selector': '.content-publication-data__from',
                'date_selector': '.content-publication-data__updated',
            },
            {
                'source_name': 'UOL Notícias',
                'title_selector': 'h1, h2',
                'content_selector': '.text',
                'author_selector': '.author',
                'date_selector': '.date',
            },
            {
                'source_name': 'CNN Brasil',
                'title_selector': 'h1, h2',
                'content_selector': '.content-text',
                'author_selector': '.author-name',
                'date_selector': '.published-date',
            }
        ]
        
        configs_created = 0
        for config_data in scraping_configs:
            try:
                source = NewsSource.objects.get(name=config_data['source_name'])
                config, created = ScrapingConfig.objects.get_or_create(
                    source=source,
                    defaults={
                        'title_selector': config_data['title_selector'],
                        'content_selector': config_data['content_selector'],
                        'author_selector': config_data['author_selector'],
                        'date_selector': config_data['date_selector'],
                    }
                )
                if created:
                    configs_created += 1
                    self.stdout.write(f'Config de scraping criada: {source.name}')
            except NewsSource.DoesNotExist:
                self.stdout.write(f'Fonte não encontrada: {config_data["source_name"]}')
        
        self.stdout.write(f'{configs_created} configurações de scraping criadas')
        
        self.stdout.write(
            self.style.SUCCESS('ORACLO inicializado com sucesso!')
        )
        self.stdout.write('Próximos passos:')
        self.stdout.write('1. Execute as migrações: python manage.py migrate')
        self.stdout.write('2. Crie um superusuário: python manage.py createsuperuser')
        self.stdout.write('3. Acesse o admin: http://localhost:8000/admin/')
        self.stdout.write('4. Acesse o dashboard: http://localhost:8000/dashboard/')
        self.stdout.write('5. Teste a API: http://localhost:8000/api/') 