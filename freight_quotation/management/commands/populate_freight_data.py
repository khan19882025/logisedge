from django.core.management.base import BaseCommand
from freight_quotation.models import CargoType, Incoterm, ChargeType


class Command(BaseCommand):
    help = 'Populate initial data for freight quotation app'

    def handle(self, *args, **options):
        self.stdout.write('Populating freight quotation data...')

        # Populate Cargo Types
        cargo_types = [
            {
                'name': 'General Cargo',
                'description': 'General merchandise and mixed cargo'
            },
            {
                'name': 'Heavy Machinery',
                'description': 'Industrial machinery and equipment'
            },
            {
                'name': 'Perishable Goods',
                'description': 'Food items, pharmaceuticals, and temperature-sensitive cargo'
            },
            {
                'name': 'Dangerous Goods',
                'description': 'Hazardous materials requiring special handling'
            },
            {
                'name': 'Vehicles',
                'description': 'Cars, trucks, motorcycles, and other vehicles'
            },
            {
                'name': 'Electronics',
                'description': 'Electronic devices and components'
            },
            {
                'name': 'Textiles',
                'description': 'Fabrics, clothing, and textile products'
            },
            {
                'name': 'Construction Materials',
                'description': 'Building materials and construction supplies'
            }
        ]

        for cargo_data in cargo_types:
            cargo_type, created = CargoType.objects.get_or_create(
                name=cargo_data['name'],
                defaults={'description': cargo_data['description']}
            )
            if created:
                self.stdout.write(f'Created cargo type: {cargo_type.name}')
            else:
                self.stdout.write(f'Cargo type already exists: {cargo_type.name}')

        # Populate Incoterms
        incoterms = [
            {
                'code': 'EXW',
                'name': 'Ex Works',
                'description': 'Seller makes goods available at their premises. Buyer bears all costs and risks.'
            },
            {
                'code': 'FCA',
                'name': 'Free Carrier',
                'description': 'Seller delivers goods to carrier or person nominated by buyer at seller\'s premises.'
            },
            {
                'code': 'CPT',
                'name': 'Carriage Paid To',
                'description': 'Seller pays freight to named destination. Risk transfers when goods are handed to carrier.'
            },
            {
                'code': 'CIP',
                'name': 'Carriage and Insurance Paid To',
                'description': 'Seller pays freight and insurance to named destination.'
            },
            {
                'code': 'DAP',
                'name': 'Delivered at Place',
                'description': 'Seller delivers goods to named destination. Buyer handles import clearance.'
            },
            {
                'code': 'DPU',
                'name': 'Delivered at Place Unloaded',
                'description': 'Seller delivers and unloads goods at named destination.'
            },
            {
                'code': 'DDP',
                'name': 'Delivered Duty Paid',
                'description': 'Seller delivers goods cleared for import at named destination.'
            },
            {
                'code': 'FAS',
                'name': 'Free Alongside Ship',
                'description': 'Seller delivers goods alongside ship at named port. Buyer bears all costs from that point.'
            },
            {
                'code': 'FOB',
                'name': 'Free On Board',
                'description': 'Seller delivers goods on board vessel at named port. Risk transfers when goods are on board.'
            },
            {
                'code': 'CFR',
                'name': 'Cost and Freight',
                'description': 'Seller pays freight to named port. Risk transfers when goods are on board.'
            },
            {
                'code': 'CIF',
                'name': 'Cost, Insurance and Freight',
                'description': 'Seller pays freight and insurance to named port.'
            }
        ]

        for incoterm_data in incoterms:
            incoterm, created = Incoterm.objects.get_or_create(
                code=incoterm_data['code'],
                defaults={
                    'name': incoterm_data['name'],
                    'description': incoterm_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created incoterm: {incoterm.code} - {incoterm.name}')
            else:
                self.stdout.write(f'Incoterm already exists: {incoterm.code} - {incoterm.name}')

        # Populate Charge Types
        charge_types = [
            {
                'name': 'Ocean Freight',
                'description': 'Basic ocean transportation charges'
            },
            {
                'name': 'Air Freight',
                'description': 'Air transportation charges'
            },
            {
                'name': 'Road Freight',
                'description': 'Road transportation charges'
            },
            {
                'name': 'Origin Charges',
                'description': 'Charges at origin port/airport'
            },
            {
                'name': 'Destination Charges',
                'description': 'Charges at destination port/airport'
            },
            {
                'name': 'Customs Clearance',
                'description': 'Customs clearance and documentation charges'
            },
            {
                'name': 'Insurance',
                'description': 'Cargo insurance charges'
            },
            {
                'name': 'Handling',
                'description': 'Cargo handling and processing charges'
            },
            {
                'name': 'Storage',
                'description': 'Warehouse and storage charges'
            },
            {
                'name': 'Documentation',
                'description': 'Documentation and administrative charges'
            },
            {
                'name': 'Fuel Surcharge',
                'description': 'Fuel surcharge and adjustment charges'
            },
            {
                'name': 'Security Surcharge',
                'description': 'Security and safety surcharges'
            }
        ]

        for charge_data in charge_types:
            charge_type, created = ChargeType.objects.get_or_create(
                name=charge_data['name'],
                defaults={'description': charge_data['description']}
            )
            if created:
                self.stdout.write(f'Created charge type: {charge_type.name}')
            else:
                self.stdout.write(f'Charge type already exists: {charge_type.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated freight quotation data!')
        ) 