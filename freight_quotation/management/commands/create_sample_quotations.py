from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from freight_quotation.models import FreightQuotation, Customer, CargoType, Incoterm, ChargeType, QuotationCharge
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Create sample freight quotations for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample freight quotations...')

        # Get or create a user
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('admin')
            user.save()
            self.stdout.write(f'Created user: {user.username}')

        # Get existing data
        cargo_types = list(CargoType.objects.all())
        incoterms = list(Incoterm.objects.all())
        charge_types = list(ChargeType.objects.all())

        if not cargo_types or not incoterms or not charge_types:
            self.stdout.write(self.style.ERROR('Please run populate_freight_data first!'))
            return

        # Create sample customers
        customers_data = [
            {
                'name': 'ABC Trading Company',
                'email': 'info@abctrading.com',
                'phone': '+971-50-123-4567',
                'address': 'Sheikh Zayed Road, Dubai, UAE',
                'country': 'UAE'
            },
            {
                'name': 'Global Logistics Ltd',
                'email': 'contact@globallogistics.com',
                'phone': '+971-55-987-6543',
                'address': 'Jebel Ali Free Zone, Dubai, UAE',
                'country': 'UAE'
            },
            {
                'name': 'Maritime Solutions',
                'email': 'sales@maritimesolutions.com',
                'phone': '+971-52-456-7890',
                'address': 'Port Rashid, Dubai, UAE',
                'country': 'UAE'
            }
        ]

        customers = []
        for customer_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                email=customer_data['email'],
                defaults=customer_data
            )
            customers.append(customer)
            if created:
                self.stdout.write(f'Created customer: {customer.name}')

        # Create sample quotations
        origins = ['Dubai, UAE', 'Jebel Ali, UAE', 'Abu Dhabi, UAE', 'Sharjah, UAE']
        destinations = ['Shanghai, China', 'Singapore', 'Rotterdam, Netherlands', 'Los Angeles, USA', 'Hamburg, Germany']
        cargo_details = [
            'Electronics and consumer goods',
            'Textiles and garments',
            'Machinery and equipment',
            'Automotive parts',
            'Construction materials'
        ]

        for i in range(5):
            customer = random.choice(customers)
            cargo_type = random.choice(cargo_types)
            incoterm = random.choice(incoterms)
            origin = random.choice(origins)
            destination = random.choice(destinations)
            cargo_detail = random.choice(cargo_details)
            mode = random.choice(['air', 'sea', 'road'])
            
            quotation = FreightQuotation.objects.create(
                customer=customer,
                cargo_type=cargo_type,
                incoterm=incoterm,
                origin=origin,
                destination=destination,
                mode_of_transport=mode,
                cargo_details=cargo_detail,
                weight=random.uniform(100, 5000),
                volume=random.uniform(1, 100),
                packages=random.randint(1, 50),
                currency='AED',
                vat_percentage=5,
                validity_date=date.today() + timedelta(days=random.randint(30, 90)),
                status=random.choice(['draft', 'sent', 'accepted']),
                created_by=user
            )

            # Add some charges
            for j in range(random.randint(2, 5)):
                charge_type = random.choice(charge_types)
                rate = random.uniform(10, 500)
                quantity = random.uniform(1, 10)
                
                QuotationCharge.objects.create(
                    quotation=quotation,
                    charge_type=charge_type,
                    description=f'{charge_type.name} for {quotation.cargo_details}',
                    currency='AED',
                    rate=rate,
                    unit=random.choice(['cbm', 'ton', 'container', 'package', 'flat']),
                    quantity=quantity
                )

            self.stdout.write(f'Created quotation: {quotation.quotation_number}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample freight quotations!')
        )
