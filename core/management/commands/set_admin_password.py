from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Define a senha do usuário admin'

    def handle(self, *args, **options):
        try:
            admin_user = User.objects.get(username='admin')
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS('Senha do admin definida como: admin123')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Usuário admin não encontrado')
            ) 