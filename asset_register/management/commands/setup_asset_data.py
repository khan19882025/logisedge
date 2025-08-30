from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from asset_register.models import (
    AssetCategory, AssetLocation, AssetStatus, AssetDepreciation, Asset
)
from decimal import Decimal


class Command(BaseCommand):
    help = 'Set up initial data for Asset Register system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Asset Register initial data...')
        
        # Create default asset statuses
        statuses = [
            {'name': 'Active', 'description': 'Asset is in use and operational', 'color': '#10b981'},
            {'name': 'Inactive', 'description': 'Asset is not currently in use', 'color': '#6b7280'},
            {'name': 'Under Repair', 'description': 'Asset is being repaired or maintained', 'color': '#f59e0b'},
            {'name': 'Disposed', 'description': 'Asset has been disposed of', 'color': '#ef4444'},
            {'name': 'Lost', 'description': 'Asset has been lost or stolen', 'color': '#dc2626'},
            {'name': 'Retired', 'description': 'Asset has been retired from service', 'color': '#7c3aed'},
        ]
        
        for status_data in statuses:
            status, created = AssetStatus.objects.get_or_create(
                name=status_data['name'],
                defaults=status_data
            )
            if created:
                self.stdout.write(f'Created status: {status.name}')
            else:
                self.stdout.write(f'Status already exists: {status.name}')
        
        # Create default asset categories
        categories = [
            {'name': 'Office Equipment', 'description': 'Computers, printers, office furniture'},
            {'name': 'Vehicles', 'description': 'Cars, trucks, forklifts'},
            {'name': 'Machinery', 'description': 'Industrial machinery and equipment'},
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Furniture', 'description': 'Office and home furniture'},
            {'name': 'Tools', 'description': 'Hand tools and power tools'},
            {'name': 'Buildings', 'description': 'Buildings and structures'},
            {'name': 'Land', 'description': 'Land and real estate'},
            {'name': 'Software', 'description': 'Software licenses and applications'},
            {'name': 'Other', 'description': 'Miscellaneous assets'},
        ]
        
        for category_data in categories:
            category, created = AssetCategory.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
        
        # Create default asset locations
        locations = [
            {'name': 'Main Office', 'building': 'Headquarters', 'floor': '1', 'room': 'General'},
            {'name': 'Warehouse A', 'building': 'Warehouse Complex', 'floor': '1', 'room': 'Storage'},
            {'name': 'Warehouse B', 'building': 'Warehouse Complex', 'floor': '1', 'room': 'Storage'},
            {'name': 'Production Floor', 'building': 'Factory', 'floor': '1', 'room': 'Production'},
            {'name': 'IT Department', 'building': 'Headquarters', 'floor': '2', 'room': 'IT Office'},
            {'name': 'Finance Department', 'building': 'Headquarters', 'floor': '2', 'room': 'Finance'},
            {'name': 'HR Department', 'building': 'Headquarters', 'floor': '2', 'room': 'HR'},
            {'name': 'Meeting Room 1', 'building': 'Headquarters', 'floor': '1', 'room': 'Conference'},
            {'name': 'Meeting Room 2', 'building': 'Headquarters', 'floor': '1', 'room': 'Conference'},
            {'name': 'Parking Lot', 'building': 'Outdoor', 'floor': 'Ground', 'room': 'Parking'},
        ]
        
        for location_data in locations:
            location, created = AssetLocation.objects.get_or_create(
                name=location_data['name'],
                defaults=location_data
            )
            if created:
                self.stdout.write(f'Created location: {location.name}')
            else:
                self.stdout.write(f'Location already exists: {location.name}')
        
        # Create default depreciation methods
        depreciation_methods = [
            {
                'name': 'Straight Line - 5 Years',
                'method': 'straight_line',
                'rate_percentage': Decimal('20.00'),
                'useful_life_years': 5,
                'salvage_value_percentage': Decimal('10.00'),
                'description': 'Standard straight-line depreciation over 5 years'
            },
            {
                'name': 'Straight Line - 10 Years',
                'method': 'straight_line',
                'rate_percentage': Decimal('10.00'),
                'useful_life_years': 10,
                'salvage_value_percentage': Decimal('10.00'),
                'description': 'Standard straight-line depreciation over 10 years'
            },
            {
                'name': 'Declining Balance - 20%',
                'method': 'declining_balance',
                'rate_percentage': Decimal('20.00'),
                'useful_life_years': 5,
                'salvage_value_percentage': Decimal('10.00'),
                'description': 'Declining balance depreciation at 20% per year'
            },
            {
                'name': 'No Depreciation',
                'method': 'none',
                'rate_percentage': Decimal('0.00'),
                'useful_life_years': 0,
                'salvage_value_percentage': Decimal('0.00'),
                'description': 'Assets that do not depreciate (land, some investments)'
            },
        ]
        
        for dep_method_data in depreciation_methods:
            dep_method, created = AssetDepreciation.objects.get_or_create(
                name=dep_method_data['name'],
                defaults=dep_method_data
            )
            if created:
                self.stdout.write(f'Created depreciation method: {dep_method.name}')
            else:
                self.stdout.write(f'Depreciation method already exists: {dep_method.name}')
        
        # Create sample assets if no assets exist
        if Asset.objects.count() == 0:
            self.stdout.write('Creating sample assets...')
            
            # Get default values
            default_category = AssetCategory.objects.first()
            default_location = AssetLocation.objects.first()
            active_status = AssetStatus.objects.filter(name='Active').first()
            default_depreciation = AssetDepreciation.objects.filter(method='straight_line').first()
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if all([default_category, default_location, active_status, default_depreciation, admin_user]):
                sample_assets = [
                    {
                        'asset_name': 'Dell Latitude Laptop',
                        'description': 'High-performance laptop for office use',
                        'category': default_category,
                        'location': default_location,
                        'status': active_status,
                        'purchase_date': '2024-01-15',
                        'purchase_value': Decimal('2500.00'),
                        'current_value': Decimal('2000.00'),
                        'salvage_value': Decimal('250.00'),
                        'depreciation_method': default_depreciation,
                        'useful_life_years': 5,
                        'serial_number': 'DL123456789',
                        'model_number': 'Latitude 5520',
                        'manufacturer': 'Dell Inc.',
                        'assigned_to': admin_user,
                        'created_by': admin_user,
                    },
                    {
                        'asset_name': 'HP LaserJet Printer',
                        'description': 'Office printer for document printing',
                        'category': default_category,
                        'location': default_location,
                        'status': active_status,
                        'purchase_date': '2024-02-01',
                        'purchase_value': Decimal('800.00'),
                        'current_value': Decimal('700.00'),
                        'salvage_value': Decimal('80.00'),
                        'depreciation_method': default_depreciation,
                        'useful_life_years': 5,
                        'serial_number': 'HP987654321',
                        'model_number': 'LaserJet Pro M404n',
                        'manufacturer': 'HP Inc.',
                        'created_by': admin_user,
                    },
                    {
                        'asset_name': 'Office Desk',
                        'description': 'Standard office desk for workspace',
                        'category': AssetCategory.objects.filter(name='Furniture').first() or default_category,
                        'location': default_location,
                        'status': active_status,
                        'purchase_date': '2024-01-10',
                        'purchase_value': Decimal('500.00'),
                        'current_value': Decimal('450.00'),
                        'salvage_value': Decimal('50.00'),
                        'depreciation_method': default_depreciation,
                        'useful_life_years': 10,
                        'manufacturer': 'Office Furniture Co.',
                        'created_by': admin_user,
                    },
                ]
                
                for asset_data in sample_assets:
                    asset = Asset.objects.create(**asset_data)
                    self.stdout.write(f'Created sample asset: {asset.asset_name} ({asset.asset_code})')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up Asset Register initial data!')
        ) 