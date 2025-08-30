from django.core.management.base import BaseCommand
from documentation.models import Documentation


class Command(BaseCommand):
    help = 'Update job_no field for existing documentation records from their cargo items'

    def handle(self, *args, **options):
        self.stdout.write('Starting to update documentation job numbers...')
        
        # Get all documentation records without job_no
        docs_without_job_no = Documentation.objects.filter(job_no='')
        total_docs = docs_without_job_no.count()
        
        if total_docs == 0:
            self.stdout.write(self.style.SUCCESS('No documentation records found without job numbers.'))
            return
        
        self.stdout.write(f'Found {total_docs} documentation records without job numbers.')
        
        updated_count = 0
        for doc in docs_without_job_no:
            if doc.update_job_no_from_cargo():
                updated_count += 1
                self.stdout.write(f'Updated job number for documentation {doc.document_no}: {doc.job_no}')
            else:
                self.stdout.write(f'Could not update job number for documentation {doc.document_no} (no cargo items found)')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} out of {total_docs} documentation records.'
            )
        ) 