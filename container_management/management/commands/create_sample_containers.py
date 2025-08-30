from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random

from container_management.models import (
    Container, ContainerBooking, ContainerTracking, 
    ContainerInventory, ContainerMovement, ContainerNotification
)
from freight_quotation.models import Customer


class Command(BaseCommand):
    help = 'Create sample data for Container Management module'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample container data...')
        
        # Create sample customers if they don't exist
        customers = []
        customer_names = [
            'ABC Trading Co.', 'XYZ Logistics Ltd.', 'Global Shipping Inc.',
            'Maritime Solutions', 'Ocean Freight Services', 'Cargo Express Ltd.',
            'International Trade Co.', 'Seabound Logistics', 'Portside Shipping',
            'Marine Cargo Solutions'
        ]
        
        for name in customer_names:
            customer, created = Customer.objects.get_or_create(
                name=name,
                defaults={
                    'email': f'{name.lower().replace(" ", "").replace(".", "").replace(",", "")}@example.com',
                    'phone': f'+971-5{random.randint(10000000, 99999999)}',
                    'address': f'Address for {name}',
                    'country': 'UAE'
                }
            )
            customers.append(customer)
            if created:
                self.stdout.write(f'Created customer: {name}')
        
        # Container types and sizes
        container_types = [
            ('20ft', 'Standard 20ft Container'),
            ('40ft', 'Standard 40ft Container'),
            ('40hc', '40ft High Cube Container'),
            ('reefer', 'Refrigerated Container'),
            ('open_top', 'Open Top Container'),
            ('flat_rack', 'Flat Rack Container'),
        ]
        
        # Ports
        ports = [
            'Jebel Ali Port', 'Port Rashid', 'Khalifa Port', 'Mina Zayed',
            'Port Saqr', 'Port of Fujairah', 'Port of Khor Fakkan'
        ]
        
        # Create sample containers
        containers = []
        for i in range(50):
            container_type, container_type_display = random.choice(container_types)
            status = random.choice(['available', 'booked', 'in_use', 'maintenance'])
            
            container = Container.objects.create(
                container_number=f'UACU{random.randint(100000, 999999)}',
                container_type=container_type,
                size=container_type.split('ft')[0] if 'ft' in container_type else '40',
                tare_weight=random.randint(2000, 4000),
                max_payload=random.randint(20000, 30000),
                status=status,
                current_location=random.choice(ports),
                yard_location=f'Yard {chr(65 + random.randint(0, 5))}{random.randint(1, 10)}',
                line_operator=f'Line {chr(65 + random.randint(0, 25))}',
                last_maintenance=timezone.now().date() - timedelta(days=random.randint(30, 365)),
                next_maintenance=timezone.now().date() + timedelta(days=random.randint(30, 180)),
                notes=f'Sample container {i+1}'
            )
            containers.append(container)
        
        self.stdout.write(f'Created {len(containers)} containers')
        
        # Create sample container bookings
        bookings = []
        for i in range(30):
            container = random.choice(containers)
            customer = random.choice(customers)
            status = random.choice(['pending', 'confirmed', 'active', 'completed', 'cancelled'])
            
            booking_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
            pickup_date = booking_date + timedelta(days=random.randint(1, 30))
            delivery_date = pickup_date + timedelta(days=random.randint(1, 45))
            
            booking = ContainerBooking.objects.create(
                container=container,
                customer=customer,
                container_type=container.container_type,
                container_size=container.size,
                pickup_date=pickup_date,
                pickup_location=random.choice(ports),
                drop_off_port=random.choice(ports),
                drop_off_date=delivery_date,
                cargo_description=f'Sample cargo for booking {i+1}',
                weight=random.randint(1000, 20000),
                volume=random.randint(10, 100),
                status=status,
                rate=random.randint(100, 500),
                special_instructions=f'Special requirements for booking {i+1}',
                soc_coc_details=f'SOC/COC details for booking {i+1}'
            )
            bookings.append(booking)
        
        self.stdout.write(f'Created {len(bookings)} container bookings')
        
        # Create sample container tracking events
        tracking_events = []
        milestones = ['gate_in', 'gate_out', 'on_vessel', 'at_destination', 'delivered']
        
        for i in range(100):
            container = random.choice(containers)
            booking = random.choice(bookings) if bookings else None
            milestone = random.choice(milestones)
            location = random.choice(ports)
            
            tracking = ContainerTracking.objects.create(
                container_booking=booking,
                container=container,
                milestone=milestone,
                location=location,
                event_date=timezone.now() - timedelta(days=random.randint(1, 30)),
                eta=timezone.now() + timedelta(days=random.randint(1, 15)),
                is_completed=milestone in ['delivered'],
                notes=f'Tracking event {i+1} for {milestone}'
            )
            tracking_events.append(tracking)
        
        self.stdout.write(f'Created {len(tracking_events)} tracking events')
        
        # Create sample container inventory records
        inventory_records = []
        for i in range(40):
            container = random.choice(containers)
            port = random.choice(ports)
            is_overstayed = random.choice([True, False])
            
            inventory = ContainerInventory.objects.create(
                container=container,
                port=port,
                terminal=f'Terminal {random.randint(1, 5)}',
                yard=f'Yard {chr(65 + random.randint(0, 5))}{random.randint(1, 10)}',
                status=random.choice(['empty', 'stuffed', 'loaded', 'in_transit', 'at_port', 'returned', 'overstayed']),
                arrival_date=timezone.now() - timedelta(days=random.randint(1, 60)),
                expected_departure=timezone.now() + timedelta(days=random.randint(1, 30)),
                is_overstayed=is_overstayed,
                overstay_days=random.randint(1, 15) if is_overstayed else 0,
                notes=f'Inventory record {i+1}'
            )
            inventory_records.append(inventory)
        
        self.stdout.write(f'Created {len(inventory_records)} inventory records')
        
        # Create sample container movements
        movements = []
        movement_types = ['gate_in', 'gate_out', 'vessel_load', 'vessel_unload', 'yard_transfer']
        
        for i in range(80):
            container = random.choice(containers)
            movement_type = random.choice(movement_types)
            from_location = random.choice(ports)
            to_location = random.choice(ports)
            
            movement = ContainerMovement.objects.create(
                container=container,
                movement_type=movement_type,
                from_location=from_location,
                to_location=to_location,
                movement_date=timezone.now() - timedelta(days=random.randint(1, 45)),
                vessel_name=f'Vessel {chr(65 + random.randint(0, 25))}{random.randint(100, 999)}' if 'vessel' in movement_type else '',
                voyage_number=f'VOY{random.randint(10000, 99999)}' if 'vessel' in movement_type else '',
                notes=f'Movement {i+1}: {movement_type}'
            )
            movements.append(movement)
        
        self.stdout.write(f'Created {len(movements)} container movements')
        
        # Create sample notifications
        notifications = []
        notification_types = ['overstay_alert', 'maintenance_due', 'booking_confirmation', 'status_update']
        
        for i in range(25):
            container = random.choice(containers)
            notification_type = random.choice(notification_types)
            
            notification = ContainerNotification.objects.create(
                container=container,
                notification_type=notification_type,
                title=f'{notification_type.replace("_", " ").title()} for {container.container_number}',
                message=f'Sample notification {i+1} for {notification_type}',
                is_read=random.choice([True, False]),
                priority=random.choice(['low', 'medium', 'high'])
            )
            notifications.append(notification)
        
        self.stdout.write(f'Created {len(notifications)} notifications')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {len(containers)} containers\n'
                f'- {len(bookings)} bookings\n'
                f'- {len(tracking_events)} tracking events\n'
                f'- {len(inventory_records)} inventory records\n'
                f'- {len(movements)} movements\n'
                f'- {len(notifications)} notifications'
            )
        )
