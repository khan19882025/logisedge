from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rf_scanner.models import RFUser, Location, Item


class Command(BaseCommand):
    help = 'Set up sample data for RF Scanner app'

    def handle(self, *args, **options):
        self.stdout.write('Setting up RF Scanner sample data...')

        # Create sample locations
        locations = [
            {'code': 'A1-01', 'name': 'Aisle A1, Rack 01', 'type': 'Rack'},
            {'code': 'A1-02', 'name': 'Aisle A1, Rack 02', 'type': 'Rack'},
            {'code': 'A2-01', 'name': 'Aisle A2, Rack 01', 'type': 'Rack'},
            {'code': 'B1-01', 'name': 'Aisle B1, Rack 01', 'type': 'Rack'},
            {'code': 'RECV', 'name': 'Receiving Area', 'type': 'Area'},
            {'code': 'SHIP', 'name': 'Shipping Area', 'type': 'Area'},
        ]

        for loc_data in locations:
            location, created = Location.objects.get_or_create(
                location_code=loc_data['code'],
                defaults={
                    'location_name': loc_data['name'],
                    'location_type': loc_data['type']
                }
            )
            if created:
                self.stdout.write(f'Created location: {location.location_code}')

        # Create sample items
        items = [
            {'code': 'ITEM001', 'name': 'Laptop Computer', 'barcode': '1234567890123', 'unit': 'PCS'},
            {'code': 'ITEM002', 'name': 'Wireless Mouse', 'barcode': '1234567890124', 'unit': 'PCS'},
            {'code': 'ITEM003', 'name': 'USB Cable', 'barcode': '1234567890125', 'unit': 'PCS'},
            {'code': 'ITEM004', 'name': 'Monitor Stand', 'barcode': '1234567890126', 'unit': 'PCS'},
            {'code': 'ITEM005', 'name': 'Keyboard', 'barcode': '1234567890127', 'unit': 'PCS'},
        ]

        for item_data in items:
            item, created = Item.objects.get_or_create(
                item_code=item_data['code'],
                defaults={
                    'item_name': item_data['name'],
                    'barcode': item_data['barcode'],
                    'unit': item_data['unit']
                }
            )
            if created:
                self.stdout.write(f'Created item: {item.item_code}')

        # Create sample RF Users with full names
        rf_users_data = [
            {
                'username': 'john.doe',
                'first_name': 'John',
                'last_name': 'Doe',
                'employee_id': 'EMP001',
                'department': 'Warehouse',
                'password': 'rfscanner123'
            },
            {
                'username': 'jane.smith',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'employee_id': 'EMP002',
                'department': 'Warehouse',
                'password': 'rfscanner123'
            },
            {
                'username': 'mike.wilson',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'employee_id': 'EMP003',
                'department': 'Warehouse',
                'password': 'rfscanner123'
            },
            {
                'username': 'sarah.johnson',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'employee_id': 'EMP004',
                'department': 'Warehouse',
                'password': 'rfscanner123'
            }
        ]

        for user_data in rf_users_data:
            # Check if RFUser with this employee_id already exists
            existing_rf_user = RFUser.objects.filter(employee_id=user_data['employee_id']).first()
            if existing_rf_user:
                self.stdout.write(f'RF User with Employee ID {user_data["employee_id"]} already exists: {existing_rf_user}')
                continue
            
            # Create or get user
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'email': f"{user_data['username']}@logisedge.com"
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'Created user: {user.get_full_name()}')
            
            # Create RF User profile
            rf_user, created = RFUser.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': user_data['employee_id'],
                    'department': user_data['department']
                }
            )
            if created:
                self.stdout.write(f'Created RF User: {rf_user.employee_id} - {user.get_full_name()}')

        # Create RF User for admin if it doesn't exist
        try:
            admin_user = User.objects.get(username='admin')
            # Check if admin already has RF profile
            if not hasattr(admin_user, 'rf_profile'):
                rf_user, created = RFUser.objects.get_or_create(
                    user=admin_user,
                    defaults={
                        'employee_id': 'ADMIN001',
                        'department': 'Administration'
                    }
                )
                if created:
                    self.stdout.write(f'Created RF User for admin: {rf_user.employee_id}')
            else:
                self.stdout.write(f'Admin already has RF profile: {admin_user.rf_profile.employee_id}')
        except User.DoesNotExist:
            self.stdout.write('Admin user not found. Please create an admin user first.')

        self.stdout.write(
            self.style.SUCCESS('Successfully set up RF Scanner sample data!')
        )
        self.stdout.write(
            self.style.WARNING('\nTest Login Credentials:')
        )
        self.stdout.write('Employee ID: EMP001, Name: John Doe, Password: rfscanner123')
        self.stdout.write('Employee ID: EMP002, Name: Jane Smith, Password: rfscanner123')
        self.stdout.write('Employee ID: EMP003, Name: Mike Wilson, Password: rfscanner123')
        self.stdout.write('Employee ID: EMP004, Name: Sarah Johnson, Password: rfscanner123') 