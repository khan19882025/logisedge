# Generated manually for cash_flow_statement app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '__first__'),
        ('company', '0001_initial'),
        ('fiscal_year', '0001_initial'),
        ('multi_currency', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CashFlowCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Category name', max_length=200)),
                ('category_type', models.CharField(choices=[('OPERATING', 'Operating Activities'), ('INVESTING', 'Investing Activities'), ('FINANCING', 'Financing Activities')], max_length=20)),
                ('description', models.TextField(blank=True, help_text='Category description')),
                ('display_order', models.PositiveIntegerField(default=0, help_text='Display order in reports')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Cash Flow Category',
                'verbose_name_plural': 'Cash Flow Categories',
                'ordering': ['category_type', 'display_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='CashFlowItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Item name', max_length=200)),
                ('item_type', models.CharField(choices=[('INCOME', 'Income'), ('EXPENSE', 'Expense'), ('ASSET', 'Asset'), ('LIABILITY', 'Liability'), ('EQUITY', 'Equity')], max_length=20)),
                ('calculation_method', models.CharField(default='DIRECT', help_text='How to calculate this item (DIRECT, INDIRECT, CUSTOM)', max_length=50)),
                ('account_codes', models.JSONField(blank=True, default=list, help_text='Chart of account codes to include')),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_subtotal', models.BooleanField(default=False, help_text='Whether this is a subtotal line')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='cash_flow_statement.cashflowcategory')),
            ],
            options={
                'verbose_name': 'Cash Flow Item',
                'verbose_name_plural': 'Cash Flow Items',
                'ordering': ['category__display_order', 'display_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='CashFlowStatement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Report name', max_length=200)),
                ('description', models.TextField(blank=True, help_text='Report description')),
                ('from_date', models.DateField(help_text='Start date for the report')),
                ('to_date', models.DateField(help_text='End date for the report')),
                ('report_type', models.CharField(choices=[('DETAILED', 'Detailed Report'), ('SUMMARY', 'Summary Report'), ('COMPARATIVE', 'Comparative Report')], default='DETAILED', max_length=20)),
                ('export_format', models.CharField(choices=[('PDF', 'PDF'), ('EXCEL', 'Excel'), ('CSV', 'CSV')], default='PDF', max_length=10)),
                ('include_comparative', models.BooleanField(default=False, help_text='Include comparative period')),
                ('include_notes', models.BooleanField(default=True, help_text='Include explanatory notes')),
                ('include_charts', models.BooleanField(default=True, help_text='Include charts and graphs')),
                ('is_saved', models.BooleanField(default=False, help_text='Whether this report is saved')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cash_flow_statements', to='company.company')),
                ('currency', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='multi_currency.currency')),
                ('fiscal_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cash_flow_statements', to='fiscal_year.fiscalyear')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cash_flow_reports_created', to='auth.user')),
            ],
            options={
                'verbose_name': 'Cash Flow Statement',
                'verbose_name_plural': 'Cash Flow Statements',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CashFlowTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Template name', max_length=200)),
                ('description', models.TextField(blank=True, help_text='Template description')),
                ('template_type', models.CharField(choices=[('STANDARD', 'Standard Template'), ('CUSTOM', 'Custom Template'), ('INDUSTRY', 'Industry Specific')], default='STANDARD', max_length=20)),
                ('include_operating_activities', models.BooleanField(default=True)),
                ('include_investing_activities', models.BooleanField(default=True)),
                ('include_financing_activities', models.BooleanField(default=True)),
                ('custom_operating_items', models.JSONField(blank=True, default=list)),
                ('custom_investing_items', models.JSONField(blank=True, default=list)),
                ('custom_financing_items', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('is_public', models.BooleanField(default=False, help_text='Available to all users')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cash_flow_templates_created', to='auth.user')),
            ],
            options={
                'verbose_name': 'Cash Flow Template',
                'verbose_name_plural': 'Cash Flow Templates',
                'ordering': ['name'],
            },
        ),
    ] 