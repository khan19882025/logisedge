# Generated manually for Ledger model updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0002_alter_ledger_amount'),
        ('payment_source', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ledger',
            name='payment_source',
            field=models.ForeignKey(blank=True, help_text='Payment source from invoice', null=True, on_delete=django.db.models.deletion.SET_NULL, to='payment_source.paymentsource'),
        ),
    ]
