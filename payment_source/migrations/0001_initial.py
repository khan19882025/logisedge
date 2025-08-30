# Generated manually for PaymentSource model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Payment Source Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active Status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_sources_created', to='auth.user', verbose_name='Created By')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_sources_updated', to='auth.user', verbose_name='Updated By')),
            ],
            options={
                'verbose_name': 'Payment Source',
                'verbose_name_plural': 'Payment Sources',
                'db_table': 'payment_source',
                'ordering': ['name'],
            },
        ),
    ]
