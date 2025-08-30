from django.core.management.base import BaseCommand
from payroll.models import SalaryStructure
from django.db import transaction


class Command(BaseCommand):
    help = 'Create sample salary structures for testing the payroll system'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Sample salary structures data
            structures_data = [
                {
                    'name': 'Entry Level',
                    'description': 'Entry level positions with basic salary structure',
                    'basic_salary': 5000.00,
                    'housing_allowance': 2000.00,
                    'transport_allowance': 500.00,
                    'other_allowances': 300.00,
                },
                {
                    'name': 'Mid Level',
                    'description': 'Mid-level positions with competitive salary structure',
                    'basic_salary': 8000.00,
                    'housing_allowance': 3000.00,
                    'transport_allowance': 800.00,
                    'other_allowances': 500.00,
                },
                {
                    'name': 'Senior Level',
                    'description': 'Senior positions with comprehensive salary structure',
                    'basic_salary': 12000.00,
                    'housing_allowance': 4000.00,
                    'transport_allowance': 1000.00,
                    'other_allowances': 800.00,
                },
                {
                    'name': 'Manager Level',
                    'description': 'Managerial positions with premium salary structure',
                    'basic_salary': 15000.00,
                    'housing_allowance': 5000.00,
                    'transport_allowance': 1200.00,
                    'other_allowances': 1000.00,
                },
                {
                    'name': 'Executive Level',
                    'description': 'Executive positions with top-tier salary structure',
                    'basic_salary': 20000.00,
                    'housing_allowance': 6000.00,
                    'transport_allowance': 1500.00,
                    'other_allowances': 1500.00,
                },
            ]

            created_count = 0
            for structure_data in structures_data:
                # Check if structure already exists
                if not SalaryStructure.objects.filter(name=structure_data['name']).exists():
                    structure = SalaryStructure.objects.create(**structure_data)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created salary structure: {structure.name} (CTC: {structure.total_ctc})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Salary structure already exists: {structure_data["name"]}'
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} new salary structures'
                )
            ) 