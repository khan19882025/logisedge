# Generated manually for Invoice model updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0009_invoice_due_date'),
        ('payment_source', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='payment_source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payment_source.paymentsource', verbose_name='Payment Source'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='is_posted',
            field=models.BooleanField(default=False, verbose_name='Posted to Ledger'),
        ),
    ]
