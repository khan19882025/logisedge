# Generated manually for PaymentSource model updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payment_source', '0001_initial'),
        ('chart_of_accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentsource',
            name='payment_type',
            field=models.CharField(
                choices=[
                    ('prepaid', 'Prepaid'),
                    ('postpaid', 'Postpaid'),
                    ('cash_bank', 'Cash/Bank'),
                ],
                default='postpaid',
                help_text='Type of payment arrangement',
                max_length=20,
                verbose_name='Payment Type'
            ),
        ),
        migrations.AddField(
            model_name='paymentsource',
            name='linked_account',
            field=models.ForeignKey(
                blank=True,
                help_text='Chart of Account linked to this payment source',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='chart_of_accounts.chartofaccount',
                verbose_name='Linked Account'
            ),
        ),
    ]
