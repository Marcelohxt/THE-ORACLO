# ORACLO - Sistema de Coleta e Análise de Notícias

ORACLO é uma ferramenta avançada desenvolvida em Django e Python para coleta, análise e distribuição de informações em tempo real a partir de múltiplas fontes globais de notícias e redes sociais.

## 🚀 Características Principais

### 📊 Coleta de Dados
- **Web Scraping**: Coleta automática de notícias de websites
- **RSS Feeds**: Suporte a feeds RSS/Atom
- **APIs**: Integração com APIs públicas e privadas
- **Redes Sociais**: Coleta de dados do Twitter/X, Telegram, etc.
- **Múltiplas Fontes**: Suporte a centenas de fontes simultâneas

### 🧠 Processamento Inteligente
- **Análise de Sentimento**: VADER, TextBlob, Transformers
- **Extração de Entidades**: spaCy, NLTK, Regex
- **Extração de Palavras-chave**: TF-IDF, YAKE, RAKE
- **Classificação Automática**: ML para categorização
- **Score de Qualidade**: Métricas de qualidade de conteúdo
- **Detecção de Duplicatas**: Identificação de notícias similares

### 📈 Análise e Insights
- **Tendências**: Identificação de tópicos em alta
- **Alertas Inteligentes**: Notificações baseadas em eventos
- **Estatísticas Avançadas**: Métricas detalhadas de performance
- **Dashboards Interativos**: Visualizações em tempo real

### 🔧 Tecnologias Utilizadas

#### Backend
- **Django 5.0**: Framework web principal
- **Django REST Framework**: API REST
- **PostgreSQL**: Banco de dados principal
- **Redis**: Cache e filas
- **Celery**: Processamento assíncrono

#### Coleta de Dados
- **requests/aiohttp**: Requisições HTTP
- **BeautifulSoup**: Parse HTML
- **Selenium/Playwright**: Automação web
- **Scrapy**: Framework de scraping
- **feedparser**: Parse RSS/Atom

#### Processamento
- **NLTK**: Processamento de linguagem natural
- **spaCy**: NLP industrial
- **scikit-learn**: Machine Learning
- **VADER**: Análise de sentimento
- **YAKE**: Extração de keywords

## 📋 Pré-requisitos

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (opcional, para frontend)

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/oraclo.git
cd oraclo
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados
```bash
# Instale o PostgreSQL e Redis
# Configure as variáveis de ambiente ou edite settings.py
```

### 5. Execute as migrações
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Inicialize o sistema
```bash
python manage.py init_oraclo
```

### 7. Crie um superusuário
```bash
python manage.py createsuperuser
```

### 8. Execute o servidor
```bash
python manage.py runserver
```

## ⚙️ Configuração

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados
DATABASE_URL=postgresql://user:password@localhost:5432/oraclo
REDIS_URL=redis://localhost:6379/0

# APIs (opcional)
OPENAI_API_KEY=sua-chave-openai
TWITTER_API_KEY=sua-chave-twitter
TWITTER_API_SECRET=sua-chave-secreta-twitter
TELEGRAM_BOT_TOKEN=seu-token-telegram

# Configurações ORACLO
ORACLO_COLLECTION_INTERVAL=300
ORACLO_MAX_ARTICLES_PER_SOURCE=100
ORACLO_ENABLE_AI_ANALYSIS=True
```

### Configuração do PostgreSQL
```sql
CREATE DATABASE oraclo;
CREATE USER oraclo_user WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE oraclo TO oraclo_user;
```

### Configuração do Redis
```bash
# Instale o Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # macOS

# Inicie o serviço
sudo systemctl start redis  # Linux
brew services start redis  # macOS
```

## 🚀 Uso

### Dashboard Web
Acesse o dashboard em: http://localhost:8000/dashboard/

### API REST
Acesse a API em: http://localhost:8000/api/

### Admin Django
Acesse o admin em: http://localhost:8000/admin/

### Comandos de Gerenciamento

#### Inicializar dados básicos
```bash
python manage.py init_oraclo
```

#### Coletar notícias
```bash
python manage.py collect_news
```

#### Processar artigos
```bash
python manage.py process_articles
```

#### Análise de sentimento
```bash
python manage.py analyze_sentiment
```

## 📊 Estrutura do Projeto

```
oraclo/
├── core/                   # App principal
│   ├── models.py          # Modelos de dados
│   ├── serializers.py     # Serializers da API
│   ├── admin.py           # Configuração do admin
│   └── management/        # Comandos personalizados
├── news_collector/        # Sistema de coleta
│   ├── models.py          # Modelos de coleta
│   ├── collectors.py      # Coletores de dados
│   └── tasks.py           # Tarefas assíncronas
├── data_processor/        # Processamento de dados
│   ├── models.py          # Modelos de processamento
│   ├── processors.py      # Processadores
│   └── pipelines.py       # Pipelines de processamento
├── api/                   # API REST
│   ├── views.py           # Views da API
│   └── urls.py            # URLs da API
├── dashboard/             # Dashboard web
│   ├── views.py           # Views do dashboard
│   └── urls.py            # URLs do dashboard
├── templates/             # Templates HTML
├── static/                # Arquivos estáticos
├── media/                 # Arquivos de mídia
├── logs/                  # Logs do sistema
└── requirements.txt       # Dependências
```

## 🔌 API Endpoints

### Artigos
- `GET /api/articles/` - Lista de artigos
- `GET /api/articles/{id}/` - Detalhes do artigo
- `GET /api/articles/breaking-news/` - Notícias de última hora
- `GET /api/articles/trending/` - Artigos em tendência

### Fontes
- `GET /api/sources/` - Lista de fontes
- `POST /api/sources/{id}/collect/` - Iniciar coleta

### Análises
- `POST /api/sentiment-analysis/` - Análise de sentimento
- `POST /api/entity-extraction/` - Extração de entidades
- `POST /api/keyword-extraction/` - Extração de keywords

### Estatísticas
- `GET /api/stats/` - Estatísticas gerais
- `GET /api/trending/` - Tendências atuais

## 📈 Monitoramento

### Logs
Os logs são salvos em `logs/oraclo.log` e incluem:
- Coletas de dados
- Processamento de artigos
- Erros e exceções
- Performance metrics

### Métricas
- Artigos coletados por hora
- Taxa de sucesso das coletas
- Tempo de processamento
- Qualidade dos dados

### Alertas
- Fontes offline
- Erros de coleta
- Picos de volume
- Mudanças de sentimento

## 🔒 Segurança

### Autenticação
- Django Admin com autenticação
- API com tokens JWT
- Permissões baseadas em roles

### Rate Limiting
- Limite de requisições por IP
- Delays entre coletas
- Proteção contra spam

### Validação de Dados
- Sanitização de HTML
- Validação de URLs
- Verificação de duplicatas

## 🚀 Deploy

### Docker
```bash
# Build da imagem
docker build -t oraclo .

# Executar container
docker run -p 8000:8000 oraclo
```

### Produção
```bash
# Configurar variáveis de produção
export DEBUG=False
export ALLOWED_HOSTS=seu-dominio.com

# Usar Gunicorn
gunicorn oraclo.wsgi:application

# Configurar Nginx
# (ver arquivo nginx.conf)
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Email**: suporte@oraclo.com
- **Documentação**: https://docs.oraclo.com
- **Issues**: https://github.com/seu-usuario/oraclo/issues

## 🙏 Agradecimentos

- Django Software Foundation
- Comunidade Python
- Contribuidores do projeto

---

**ORACLO** - Transformando dados em insights inteligentes 🌟 