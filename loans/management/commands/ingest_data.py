from django.core.management.base import BaseCommand
from loans.tasks import ingest_customer_data, ingest_loan_data


class Command(BaseCommand):
    help = 'Ingest customer and loan data from xlsx files'

    def handle(self, *args, **kwargs):
        self.stdout.write('Ingesting customer data...')
        result1 = ingest_customer_data()
        self.stdout.write(self.style.SUCCESS(result1))

        self.stdout.write('Ingesting loan data...')
        result2 = ingest_loan_data()
        self.stdout.write(self.style.SUCCESS(result2))