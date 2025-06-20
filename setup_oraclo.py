#!/usr/bin/env python
"""
Script de setup automatizado para o ORACLO
Instala dependências e configura o sistema
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Executa um comando e mostra o resultado"""
    print(f"\n🔧 {description}...")
    print(f"Comando: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✓ Sucesso!")
            if result.stdout:
                print(result.stdout)
        else:
            print("✗ Erro!")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Erro ao executar comando: {e}")
        return False
    
    return True

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    print("🐍 Verificando versão do Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"✗ Python {version.major}.{version.minor} não é compatível")
        print("✓ Necessário Python 3.8+")
        return False
    
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def check_pip():
    """Verifica se o pip está disponível"""
    print("📦 Verificando pip...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ pip disponível")
            return True
        else:
            print("✗ pip não encontrado")
            return False
    except Exception as e:
        print(f"✗ Erro ao verificar pip: {e}")
        return False

def install_dependencies():
    """Instala as dependências do projeto"""
    print("📦 Instalando dependências...")
    
    # Atualiza pip primeiro
    run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Atualizando pip"
    )
    
    # Instala dependências principais
    main_deps = [
        "django",
        "djangorestframework", 
        "django-cors-headers",
        "django-filter",
        "requests",
        "aiohttp",
        "beautifulsoup4",
        "feedparser"
    ]
    
    for dep in main_deps:
        success = run_command(
            f"{sys.executable} -m pip install {dep}",
            f"Instalando {dep}"
        )
        if not success:
            print(f"⚠ Falha ao instalar {dep}, continuando...")
    
    # Instala dependências opcionais
    optional_deps = [
        "nltk",
        "scikit-learn",
        "vaderSentiment",
        "redis",
        "psycopg2-binary"
    ]
    
    print("\n📦 Instalando dependências opcionais...")
    for dep in optional_deps:
        try:
            run_command(
                f"{sys.executable} -m pip install {dep}",
                f"Instalando {dep} (opcional)"
            )
        except:
            print(f"⚠ {dep} não pôde ser instalado, continuando...")

def setup_django():
    """Configura o Django"""
    print("⚙️ Configurando Django...")
    
    commands = [
        ("python manage.py makemigrations", "Criando migrações"),
        ("python manage.py migrate", "Executando migrações"),
        ("python manage.py collectstatic --noinput", "Coletando arquivos estáticos"),
    ]
    
    for command, description in commands:
        success = run_command(command, description)
        if not success:
            print(f"⚠ {description} falhou, continuando...")

def create_superuser():
    """Cria um superusuário"""
    print("👤 Criando superusuário...")
    
    # Verifica se já existe um superusuário
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oraclo.settings')
        django.setup()
        
        from django.contrib.auth.models import User
        if User.objects.filter(is_superuser=True).exists():
            print("✓ Superusuário já existe")
            return True
    except:
        pass
    
    # Cria superusuário padrão
    print("Criando superusuário padrão:")
    print("Usuário: admin")
    print("Email: admin@oraclo.com")
    print("Senha: admin123")
    
    # Comando para criar superusuário não-interativo
    command = (
        "echo 'from django.contrib.auth.models import User; "
        "User.objects.create_superuser(\"admin\", \"admin@oraclo.com\", \"admin123\")' | "
        "python manage.py shell"
    )
    
    return run_command(command, "Criando superusuário")

def initialize_data():
    """Inicializa dados básicos"""
    print("📊 Inicializando dados...")
    
    commands = [
        ("python manage.py init_oraclo", "Inicializando ORACLO"),
        ("python manage.py import_sources", "Importando fontes de notícias"),
    ]
    
    for command, description in commands:
        success = run_command(command, description)
        if not success:
            print(f"⚠ {description} falhou, continuando...")

def check_services():
    """Verifica se os serviços necessários estão rodando"""
    print("🔍 Verificando serviços...")
    
    # Verifica PostgreSQL (se estiver usando)
    try:
        import psycopg2
        print("✓ PostgreSQL driver disponível")
    except ImportError:
        print("⚠ PostgreSQL driver não instalado (usando SQLite)")
    
    # Verifica Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis está rodando")
    except:
        print("⚠ Redis não está rodando (opcional)")

def create_env_file():
    """Cria arquivo .env com configurações básicas"""
    print("📝 Criando arquivo .env...")
    
    env_content = """# Configurações do ORACLO
SECRET_KEY=django-insecure-oraclo-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados (SQLite por padrão)
DATABASE_URL=sqlite:///db.sqlite3

# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Configurações ORACLO
ORACLO_COLLECTION_INTERVAL=300
ORACLO_MAX_ARTICLES_PER_SOURCE=100
ORACLO_ENABLE_AI_ANALYSIS=False

# APIs (opcional)
# OPENAI_API_KEY=sua-chave-openai
# TWITTER_API_KEY=sua-chave-twitter
# TELEGRAM_BOT_TOKEN=seu-token-telegram
"""
    
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✓ Arquivo .env criado")
    else:
        print("✓ Arquivo .env já existe")

def show_next_steps():
    """Mostra os próximos passos"""
    print("\n" + "=" * 60)
    print("🎉 SETUP CONCLUÍDO!")
    print("=" * 60)
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Execute o servidor:")
    print("   python manage.py runserver")
    print()
    print("2. Acesse o admin:")
    print("   http://localhost:8000/admin/")
    print("   Usuário: admin")
    print("   Senha: admin123")
    print()
    print("3. Acesse o dashboard:")
    print("   http://localhost:8000/dashboard/")
    print()
    print("4. Teste a API:")
    print("   http://localhost:8000/api/")
    print()
    print("5. Execute testes:")
    print("   python test_oraclo.py")
    print()
    print("📚 DOCUMENTAÇÃO:")
    print("- README.md - Documentação completa")
    print("- http://localhost:8000/dashboard/api-docs/ - Documentação da API")
    print()
    print("🔧 COMANDOS ÚTEIS:")
    print("- python manage.py collect_news - Coletar notícias")
    print("- python manage.py process_articles - Processar artigos")
    print("- python manage.py shell - Shell do Django")
    print()
    print("⚠ IMPORTANTE:")
    print("- Altere a SECRET_KEY em produção")
    print("- Configure um banco PostgreSQL para produção")
    print("- Configure Redis para melhor performance")
    print("- Configure as APIs (OpenAI, Twitter, etc.)")

def main():
    """Função principal"""
    print("🚀 SETUP AUTOMATIZADO DO ORACLO")
    print("=" * 60)
    
    # Verificações iniciais
    if not check_python_version():
        return
    
    if not check_pip():
        print("✗ pip não encontrado. Instale o pip primeiro.")
        return
    
    # Setup
    install_dependencies()
    create_env_file()
    setup_django()
    create_superuser()
    initialize_data()
    check_services()
    
    # Próximos passos
    show_next_steps()

if __name__ == "__main__":
    main() 