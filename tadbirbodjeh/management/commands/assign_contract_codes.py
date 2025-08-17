from django.core.management.base import BaseCommand
from khayyam import JalaliDatetime
from tadbirbodjeh.models import Contract
from collections import defaultdict

class Command(BaseCommand):
    help = 'Assign sequential codes to contracts per Jalali year'

    def handle(self, *args, **kwargs):
        contracts = Contract.objects.exclude(document_date=None).order_by('document_date', 'id')
        yearly_counters = defaultdict(int)
        updated_count = 0

        for contract in contracts:
            if contract.code:
                continue  # Skip if already coded

            jalali_year = JalaliDatetime(contract.document_date).year
            yearly_counters[jalali_year] += 1
            contract.code = yearly_counters[jalali_year]
            contract.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"{updated_count} contract(s) updated with sequential codes."))
