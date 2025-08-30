from django.core.management.base import BaseCommand
from lgp.models import PackageType


class Command(BaseCommand):
    help = 'Populate PackageType table with initial package types'

    def handle(self, *args, **options):
        package_types = [
            {'name': 'Box', 'code': 'box', 'description': 'Standard box packaging'},
            {'name': 'Carton', 'code': 'carton', 'description': 'Cardboard carton packaging'},
            {'name': 'Pallet', 'code': 'pallet', 'description': 'Wooden or plastic pallet'},
            {'name': 'Bag', 'code': 'bag', 'description': 'Bag packaging'},
            {'name': 'Drum', 'code': 'drum', 'description': 'Cylindrical drum container'},
            {'name': 'Roll', 'code': 'roll', 'description': 'Roll packaging for flexible materials'},
            {'name': 'Piece', 'code': 'piece', 'description': 'Individual piece or unit'},
            {'name': 'Container', 'code': 'container', 'description': 'Shipping container'},
            {'name': 'Bundle', 'code': 'bundle', 'description': 'Bundle of items'},
            {'name': 'Other', 'code': 'other', 'description': 'Other packaging type'},
        ]

        created_count = 0
        for pkg_data in package_types:
            package_type, created = PackageType.objects.get_or_create(
                code=pkg_data['code'],
                defaults={
                    'name': pkg_data['name'],
                    'description': pkg_data['description'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created package type: {package_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Package type already exists: {package_type.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted! Created {created_count} new package types.')
        )