from django.core.management.base import BaseCommand
from khayyam import JalaliDatetime
from tadbirbodjeh.models import Financial
from collections import defaultdict

class Command(BaseCommand):
    help = 'Assign sequential codes to financials per Jalali year'

    def handle(self, *args, **kwargs):
        financials = Financial.objects.exclude(date_doc=None).order_by('date_doc', 'id')
        yearly_counters = defaultdict(int)
        updated_count = 0

        for financial in financials:
            if financial.code:
                continue  # Skip if already coded

            jalali_year = JalaliDatetime(financial.date_doc).year
            yearly_counters[jalali_year] += 1
            financial.code = yearly_counters[jalali_year]
            financial.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"{updated_count} financial(s) updated with sequential codes."))
