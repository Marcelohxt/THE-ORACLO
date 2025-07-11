# Generated by Django 5.2.3 on 2025-06-20 18:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProxyConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('proxy_type', models.CharField(choices=[('http', 'HTTP'), ('https', 'HTTPS'), ('socks4', 'SOCKS4'), ('socks5', 'SOCKS5')], max_length=10)),
                ('host', models.CharField(max_length=200)),
                ('port', models.IntegerField()),
                ('username', models.CharField(blank=True, max_length=200)),
                ('password', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('is_rotating', models.BooleanField(default=False)),
                ('max_requests', models.IntegerField(default=1000)),
                ('current_requests', models.IntegerField(default=0)),
                ('response_time', models.FloatField(blank=True, null=True)),
                ('success_rate', models.FloatField(default=100.0)),
                ('last_used', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='WebhookEndpoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('url', models.URLField(max_length=500)),
                ('secret_key', models.CharField(blank=True, max_length=200)),
                ('events', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('retry_count', models.IntegerField(default=3)),
                ('timeout', models.IntegerField(default=30)),
                ('total_calls', models.IntegerField(default=0)),
                ('successful_calls', models.IntegerField(default=0)),
                ('failed_calls', models.IntegerField(default=0)),
                ('last_called', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='CollectionTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('running', 'Executando'), ('completed', 'Concluída'), ('failed', 'Falhou'), ('cancelled', 'Cancelada')], default='pending', max_length=20)),
                ('scheduled_at', models.DateTimeField()),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('articles_found', models.IntegerField(default=0)),
                ('articles_collected', models.IntegerField(default=0)),
                ('articles_updated', models.IntegerField(default=0)),
                ('errors', models.JSONField(blank=True, default=list)),
                ('processing_time', models.FloatField(blank=True, null=True)),
                ('memory_usage', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collection_tasks', to='core.newssource')),
            ],
            options={
                'ordering': ['-scheduled_at'],
            },
        ),
        migrations.CreateModel(
            name='ScrapingConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_selector', models.CharField(blank=True, max_length=200)),
                ('content_selector', models.CharField(blank=True, max_length=200)),
                ('author_selector', models.CharField(blank=True, max_length=200)),
                ('date_selector', models.CharField(blank=True, max_length=200)),
                ('image_selector', models.CharField(blank=True, max_length=200)),
                ('rss_feed_url', models.URLField(blank=True, max_length=500)),
                ('api_endpoint', models.URLField(blank=True, max_length=500)),
                ('api_key', models.CharField(blank=True, max_length=200)),
                ('api_headers', models.JSONField(blank=True, default=dict)),
                ('content_cleanup_rules', models.JSONField(blank=True, default=list)),
                ('date_format', models.CharField(blank=True, max_length=50)),
                ('timezone', models.CharField(blank=True, max_length=50)),
                ('request_delay', models.FloatField(default=1.0)),
                ('max_requests_per_minute', models.IntegerField(default=60)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scraping_config', to='core.newssource')),
            ],
        ),
        migrations.CreateModel(
            name='RSSFeed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feed_url', models.URLField(max_length=500)),
                ('feed_title', models.CharField(blank=True, max_length=200)),
                ('feed_description', models.TextField(blank=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('etag', models.CharField(blank=True, max_length=200)),
                ('last_modified', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rss_feeds', to='core.newssource')),
            ],
            options={
                'unique_together': {('source', 'feed_url')},
            },
        ),
        migrations.CreateModel(
            name='SocialMediaSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('twitter', 'Twitter/X'), ('telegram', 'Telegram'), ('facebook', 'Facebook'), ('instagram', 'Instagram'), ('linkedin', 'LinkedIn'), ('youtube', 'YouTube')], max_length=20)),
                ('account_id', models.CharField(max_length=200)),
                ('account_name', models.CharField(blank=True, max_length=200)),
                ('api_key', models.CharField(blank=True, max_length=200)),
                ('api_secret', models.CharField(blank=True, max_length=200)),
                ('access_token', models.CharField(blank=True, max_length=200)),
                ('access_secret', models.CharField(blank=True, max_length=200)),
                ('max_posts', models.IntegerField(default=100)),
                ('include_retweets', models.BooleanField(default=False)),
                ('include_replies', models.BooleanField(default=False)),
                ('last_collection', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_sources', to='core.newssource')),
            ],
            options={
                'unique_together': {('source', 'platform', 'account_id')},
            },
        ),
    ]
