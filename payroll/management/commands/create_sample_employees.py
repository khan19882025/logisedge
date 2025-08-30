from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Create sample employees for testing the payroll system'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Sample employees data
            employees_data = [
                {
                    'username': 'john.doe',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john.doe@company.com',
                    'is_staff': False,
                },
                {
                    'username': 'jane.smith',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'email': 'jane.smith@company.com',
                    'is_staff': False,
                },
                {
                    'username': 'mike.johnson',
                    'first_name': 'Mike',
                    'last_name': 'Johnson',
                    'email': 'mike.johnson@company.com',
                    'is_staff': False,
                },
                {
                    'username': 'sarah.wilson',
                    'first_name': 'Sarah',
                    'last_name': 'Wilson',
                    'email': 'sarah.wilson@company.com',
                    'is_staff': False,
                },
                {
                    'username': 'ahmed.ali',
                    'first_name': 'Ahmed',
                    'last_name': 'Ali',
                    'email': 'ahmed.ali@company.com',
                    'is_staff': False,
                },
            ]

            created_count = 0
            for employee_data in employees_data:
                # Check if user already exists
                if not User.objects.filter(username=employee_data['username']).exists():
                    user = User.objects.create_user(
                        username=employee_data['username'],
                        first_name=employee_data['first_name'],
                        last_name=employee_data['last_name'],
                        email=employee_data['email'],
                        is_staff=employee_data['is_staff'],
                        password='password123'  # Default password for testing
                    )
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created employee: {user.get_full_name()} ({user.username})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Employee already exists: {employee_data["username"]}'
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} new employees'
                )
            ) 