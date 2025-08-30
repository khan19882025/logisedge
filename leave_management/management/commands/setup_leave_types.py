from django.core.management.base import BaseCommand
from leave_management.models import LeaveType, LeavePolicy


class Command(BaseCommand):
    help = 'Set up initial leave types and policies for the leave management system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial leave types...')
        
        # Create leave types
        leave_types_data = [
            {
                'name': 'Annual Leave',
                'description': 'Regular annual leave for employees',
                'color': '#28a745',
                'max_days_per_year': 30,
                'max_consecutive_days': 14,
                'min_notice_days': 3,
                'is_paid': True,
                'can_carry_forward': True,
                'max_carry_forward_days': 10,
            },
            {
                'name': 'Sick Leave',
                'description': 'Medical leave for health-related issues',
                'color': '#dc3545',
                'max_days_per_year': 15,
                'max_consecutive_days': 30,
                'min_notice_days': 0,
                'is_paid': True,
                'can_carry_forward': False,
                'max_carry_forward_days': 0,
            },
            {
                'name': 'Casual Leave',
                'description': 'Short-term personal leave',
                'color': '#ffc107',
                'max_days_per_year': 10,
                'max_consecutive_days': 3,
                'min_notice_days': 1,
                'is_paid': True,
                'can_carry_forward': False,
                'max_carry_forward_days': 0,
            },
            {
                'name': 'Maternity Leave',
                'description': 'Leave for expecting mothers',
                'color': '#e83e8c',
                'max_days_per_year': 90,
                'max_consecutive_days': 90,
                'min_notice_days': 30,
                'is_paid': True,
                'can_carry_forward': False,
                'max_carry_forward_days': 0,
            },
            {
                'name': 'Paternity Leave',
                'description': 'Leave for new fathers',
                'color': '#17a2b8',
                'max_days_per_year': 14,
                'max_consecutive_days': 14,
                'min_notice_days': 7,
                'is_paid': True,
                'can_carry_forward': False,
                'max_carry_forward_days': 0,
            },
            {
                'name': 'Unpaid Leave',
                'description': 'Leave without pay for personal reasons',
                'color': '#6c757d',
                'max_days_per_year': 30,
                'max_consecutive_days': 30,
                'min_notice_days': 7,
                'is_paid': False,
                'can_carry_forward': False,
                'max_carry_forward_days': 0,
            },
            {
                'name': 'Study Leave',
                'description': 'Leave for educational purposes',
                'color': '#6610f2',
                'max_days_per_year': 20,
                'max_consecutive_days': 20,
                'min_notice_days': 14,
                'is_paid': True,
                'can_carry_forward': False,
                'max_carry_forward_days': 0,
            },
        ]
        
        for leave_type_data in leave_types_data:
            leave_type, created = LeaveType.objects.get_or_create(
                name=leave_type_data['name'],
                defaults=leave_type_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created leave type: {leave_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Leave type already exists: {leave_type.name}')
                )
        
        # Create default leave policy
        policy_data = {
            'name': 'Standard Leave Policy',
            'description': 'Standard leave policy for all employees',
            'probation_period_months': 6,
            'annual_leave_days': 30,
            'sick_leave_days': 15,
            'casual_leave_days': 10,
            'maternity_leave_days': 90,
            'paternity_leave_days': 14,
            'carry_forward_percentage': 50,
            'encashment_allowed': True,
            'encashment_percentage': 100,
        }
        
        policy, created = LeavePolicy.objects.get_or_create(
            name=policy_data['name'],
            defaults=policy_data
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created leave policy: {policy.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Leave policy already exists: {policy.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up initial leave types and policies!')
        ) 