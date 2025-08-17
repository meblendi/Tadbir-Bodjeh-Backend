import jdatetime

from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from khayyam import JalaliDatetime  # For Jalali year extraction

class LogisticsDocumentJalaliYearFilter(SimpleListFilter):
    title = _('Created Year')  # Filter title
    parameter_name = 'date_doc_jalali_year'

    def lookups(self, request, model_admin):
        years = set()
        for logistics in model_admin.model.objects.exclude(date_doc=None):
            jalali_date = JalaliDatetime(logistics.date_doc)
            years.add(jalali_date.year)
        return [(year, str(year)) for year in sorted(years)]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            # Convert Jalali year to Gregorian year range
            try:
                jalali_start = JalaliDatetime(int(value), 1, 1).todate()
                jalali_end = JalaliDatetime(int(value), 12, 29).todate()
                return queryset.filter(date_doc__range=[jalali_start, jalali_end])
            except:
                return queryset.none()
        return queryset

class FinancialDocumentJalaliYearFilter(SimpleListFilter):
    title = _('Created Year')  # Filter title
    parameter_name = 'date_doc_jalali_year'

    def lookups(self, request, model_admin):
        years = set()
        for financial in model_admin.model.objects.exclude(date_doc=None):
            jalali_date = JalaliDatetime(financial.date_doc)
            years.add(jalali_date.year)
        return [(year, str(year)) for year in sorted(years)]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            # Convert Jalali year to Gregorian year range
            try:
                jalali_start = JalaliDatetime(int(value), 1, 1).todate()
                jalali_end = JalaliDatetime(int(value), 12, 29).todate()
                return queryset.filter(date_doc__range=[jalali_start, jalali_end])
            except:
                return queryset.none()
        return queryset

class ContractDocumentJalaliYearFilter(SimpleListFilter):
    title = _('Created Year')  # Filter title
    parameter_name = 'document_date_jalali_year'

    def lookups(self, request, model_admin):
        years = set()
        for contract in model_admin.model.objects.exclude(document_date=None):
            jalali_date = JalaliDatetime(contract.document_date)
            years.add(jalali_date.year)
        return [(year, str(year)) for year in sorted(years)]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            # Convert Jalali year to Gregorian year range
            try:
                jalali_start = JalaliDatetime(int(value), 1, 1).todate()
                jalali_end = JalaliDatetime(int(value), 12, 29).todate()
                return queryset.filter(document_date__range=[jalali_start, jalali_end])
            except:
                return queryset.none()
        return queryset
    


def to_jalali(dt):
    if not dt:
        return ''
    return jdatetime.datetime.fromgregorian(datetime=dt).strftime('%Y/%m/%d - %H:%M')