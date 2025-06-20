#!/bin/bash
set -e

# Função para aguardar o banco de dados
wait_for_db() {
    echo "Aguardando banco de dados..."
    while ! python manage.py dbshell 2>&1; do
        sleep 1
    done
    echo "Banco de dados pronto!"
}

# Função para aguardar o Redis
wait_for_redis() {
    echo "Aguardando Redis..."
    while ! python -c "import redis; redis.Redis().ping()" 2>&1; do
        sleep 1
    done
    echo "Redis pronto!"
}

# Executa migrações
echo "Executando migrações..."
python manage.py migrate

# Inicializa dados se necessário
if [ ! -f /app/.initialized ]; then
    echo "Inicializando ORACLO..."
    python manage.py init_oraclo
    python manage.py import_sources
    touch /app/.initialized
fi

# Cria superusuário se não existir
echo "Verificando superusuário..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@oraclo.com', 'admin123')
    print('Superusuário criado: admin/admin123')
else:
    print('Superusuário já existe')
"

# Executa comando passado
exec "$@" 