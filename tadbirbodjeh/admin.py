from django.contrib import admin
import tadbirbodjeh.models

# Register models
admin.site.register(tadbirbodjeh.models.LogisticsUploads)
admin.site.register(tadbirbodjeh.models.PettyCash)
admin.site.register(tadbirbodjeh.models.organization)
admin.site.register(tadbirbodjeh.models.unit)
admin.site.register(tadbirbodjeh.models.sub_unit)
admin.site.register(tadbirbodjeh.models.budget_chapter)
admin.site.register(tadbirbodjeh.models.budget_section)
admin.site.register(tadbirbodjeh.models.budget_row)
admin.site.register(tadbirbodjeh.models.Contractor_type)
admin.site.register(tadbirbodjeh.models.Contract_record)
admin.site.register(tadbirbodjeh.models.program)
# admin.site.register(tadbirbodjeh.models.Logistics)
# admin.site.register(tadbirbodjeh.models.Financial)
# admin.site.register(tadbirbodjeh.models.Contract)

# Customize admin titles
admin.site.site_header = "پنل مدیریت سامانه"
admin.site.site_title = "پنل مدیریت سامانه"
admin.site.index_title = "خوش آمدید به پنل مدیریتی"


# Optional: Add custom admin functionality for specific models
class tadbirAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "completed")


# Convert Gregorian Date widget into Jalai Date
from jalali_date.admin import ModelAdminJalaliMixin
from jalali_date.widgets import AdminJalaliDateWidget
from .dates import ContractDocumentJalaliYearFilter, FinancialDocumentJalaliYearFilter, LogisticsDocumentJalaliYearFilter
from django import forms
from .models import Contract, Financial, Logistics, Sign

class LogisticsAdminForm(forms.ModelForm):
    class Meta:
        model = Logistics
        fields = '__all__'        

@admin.register(Logistics)
class LogisticsAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = LogisticsAdminForm
    list_display = ('name', 'date_doc_jalali', 'created_jalali', 'updated_jalali')
    list_filter = (LogisticsDocumentJalaliYearFilter, 'type',)    
    ordering = ('-date_doc',)  # Default ordering
    

class FinancialAdminForm(forms.ModelForm):
    class Meta:
        model = Financial
        fields = '__all__'        

@admin.register(Financial)
class FinancialAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = FinancialAdminForm
    list_display = ('name', 'code', 'created_by', 'date_doc_jalali', 'created_jalali')
    list_filter = (FinancialDocumentJalaliYearFilter,)
    readonly_fields = ('code',)  # Make code read-only in admin
    ordering = ('-date_doc',)  # Default ordering
    # list_editable = ('code',)
    

class ContractAdminForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = '__all__'        

@admin.register(Contract)
class ContractAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = ContractAdminForm
    list_display = ('name', 'code', 'Contractor_type', 'document_date_jalali', 'created_jalali', 'updated_jalali')
    list_filter = (ContractDocumentJalaliYearFilter, 'Contractor_level', 'Contractor_type')
    readonly_fields = ('code',)  # Make code read-only in admin
    ordering = ('-document_date',)  # Default ordering
    

class SignAdminForm(forms.ModelForm):
    class Meta:
        model = Sign
        fields = '__all__'        

@admin.register(Sign)
class SignAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    form = SignAdminForm
    list_display = ('last_name', 'name', 'role', 'date_start', 'date_end')     
    list_filter = ('role',)