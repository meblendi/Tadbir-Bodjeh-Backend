import enum

from django.contrib.auth.models import User
from django.db import models

from .dates import to_jalali  # adjust the import path accordingly
from khayyam import JalaliDatetime




class fin_state(enum.Enum):
    start = 0
    cheek = 1
    final = 2


class LogisticsUploads(models.Model):
    file = models.FileField(upload_to="./uploads/", max_length=1000)
    name = models.CharField(max_length=255, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='LogisticsUploads', null=True)

    
    def __str__(self) -> str:
        return self.name


class PettyCash(models.Model):
    name = models.CharField(max_length=255, blank=True)
    doc_num = models.CharField(max_length=255, blank=True)
    date_doc = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    price = models.FloatField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='pettycash', null=True)
    F_conf = models.BooleanField(blank=True, null=True)
    L_conf = models.BooleanField(blank=True, null=True)
    descr = models.TextField(blank=True)
    forwhom = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='pettycashowner', null=True)

    def __str__(self) -> str:
        return self.name


class budget_chapter(models.Model):
    code = models.IntegerField(blank=True, null=True, default=0)
    fin_code = models.IntegerField(blank=True, null=True, default=0)
    name = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self) -> str:
        return self.name


class budget_section(models.Model):
    code = models.IntegerField(blank=True, null=True, default=0)
    fin_code = models.IntegerField(blank=True, null=True, default=0)
    name = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    budget_chapter = models.ForeignKey(budget_chapter, on_delete=models.SET_NULL, related_name='budget_section', null=True)

    def __str__(self) -> str:
        return self.name


class budget_row(models.Model):
    code = models.IntegerField(blank=True, null=True, default=0)
    fin_code = models.IntegerField(blank=True, null=True, default=0)
    name = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    budget_section = models.ForeignKey(budget_section, on_delete=models.SET_NULL, related_name='budget_row', null=True)

    def __str__(self) -> str:
        return self.name


class organization(models.Model):
    code = models.IntegerField(blank=True, null=True, default=0)
    name = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class unit(models.Model):
    code = models.IntegerField(blank=True, null=True, default=0)
    name = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    organization = models.ForeignKey(organization, on_delete=models.SET_NULL, related_name='unit', null=True)

    def __str__(self) -> str:
        return self.name


class sub_unit(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    code = models.IntegerField(blank=True, null=True, default=0)
    year = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    unit = models.ForeignKey(unit, on_delete=models.SET_NULL, related_name='sub_unit', null=True)

    def __str__(self) -> str:
        return self.name


class program(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    year = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True, default=0)
    fin_code = models.CharField(max_length=255, blank=True, null=True, default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    general_cost = models.CharField(max_length=255, blank=True, null=True, default=0)
    specific_cost = models.CharField(max_length=255, blank=True, null=True, default=0)
    other_cost = models.CharField(max_length=255, blank=True, null=True, default=0)

    def __str__(self) -> str:
        return self.name

class relation(models.Model):
    year = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    budget_row = models.ForeignKey(budget_row, on_delete=models.SET_NULL, related_name='relations', null=True)
    organization = models.ManyToManyField(organization, related_name='relations')
    programs = models.ManyToManyField(program, related_name='relations')
    # cost_type = models.CharField(max_length=255, blank=True, null=True)


class Contractor_type(models.Model):
    name = models.CharField(max_length=255, blank=True)
    Contractor_level = models.CharField(null=True, max_length=2)
    def __str__(self) -> str:
        return self.name


class Contract_record(models.Model):
    
    Contract = models.ForeignKey("Contract", on_delete=models.SET_NULL, related_name='contract_record', null=True)
    descr = models.TextField(null=True, max_length=255)
    Contractor_level = models.CharField(null=True, max_length=2)
    requested_performance_amount = models.FloatField(max_length=255, null=True)
    treasury_deduction_percent = models.FloatField(max_length=255, null=True)
    overhead_percentage = models.FloatField(max_length=255, null=True)
    performanceـwithholding = models.FloatField(max_length=255, null=True)
    performanceـwithholding_percentage = models.FloatField(max_length=255, null=True)
    payable_amount_after_deductions = models.FloatField(max_length=255, null=True)
    tax_percentage = models.FloatField(max_length=255, null=True)
    tax_amount = models.FloatField(max_length=255, null=True)    
    insurance = models.FloatField(max_length=255, null=True)
    advance_payment_deductions = models.FloatField(max_length=255, null=True)
    vat = models.FloatField(max_length=255, null=True)
    
    # New fields    
    last_name = models.CharField(max_length=255, null=True)
    contractor_id = models.CharField(max_length=255, null=True)
    doc_descr = models.TextField(null=True, max_length=255)
    contract_num = models.CharField(max_length=255, null=True)    
    account_number = models.CharField(max_length=255, null=True)
    bank_name = models.CharField(max_length=100, null=True, verbose_name="نام بانک")
    debt = models.FloatField(max_length=255, null=True)
    doc_date = models.CharField(max_length=255, null=True)
    
    # --------------------------------------
    profit = models.FloatField(max_length=255, null=True)  
    overtime = models.FloatField(max_length=255, null=True) 
    shift = models.FloatField(max_length=255, null=True)  
    vat_percentage = models.FloatField(max_length=255, null=True)  
    total_work_amount = models.FloatField(max_length=255, null=True)  
    
    final_payable_amount = models.FloatField(max_length=255, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='Contractor', null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)    
    
    def __str__(self) -> str:
        return f"{self.descr},{self.last_name}"
    

class Logistics(models.Model):
    name = models.CharField(max_length=255, blank=True)
    type = models.BooleanField(default=True)
    Fdoc_key = models.ForeignKey('Financial', related_name="logistics", 
                                 on_delete=models.SET_NULL, null=True)
    price = models.FloatField(blank=True, null=True)
    seller = models.CharField(max_length=255, blank=True)
    seller_id = models.CharField(max_length=255, blank=True)
    date_doc = models.DateTimeField(blank=True)
    Location = models.ForeignKey(sub_unit, on_delete=models.SET_NULL, related_name='Logistics', null=True)
    descr = models.TextField(blank=True)
    F_conf = models.BooleanField(default=False, blank=True)
    created = models.DateTimeField(auto_now_add=True, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)
    measure = models.CharField(max_length=255, null=True, blank=True)
    CostDriver = models.CharField(max_length=255, null=True, blank=True)
    uploads = models.ManyToManyField(LogisticsUploads, blank=True)
    vat = models.FloatField(blank=True, null=True)
    account_number = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='Logistics', null=True)
    budget_row = models.ForeignKey("budget_row", on_delete=models.SET_NULL, related_name='Logistics', null=True)
    program = models.ForeignKey("program", on_delete=models.SET_NULL, related_name='Logistics', null=True)    
    cost_type = models.IntegerField(blank=True, null=True)
    
    class Meta:
        verbose_name = "لیست مدارک"
        verbose_name_plural = "لیست مدارک"
    
    def __str__(self) -> str:
        return self.name
    
    # Jalali date properties
    @property
    def date_doc_jalali(self):
        return to_jalali(self.date_doc)

    @property
    def created_jalali(self):
        return to_jalali(self.created)

    @property
    def updated_jalali(self):
        return to_jalali(self.updated)
    
    @classmethod
    def get_logistics_by_year(cls, year):
        """Get all logistics for a specific Jalali year"""
        start_of_year = JalaliDatetime(year, 1, 1).todate()
        end_of_year = JalaliDatetime(year, 12, 29).todate()
        
        return cls.objects.filter(
            date_doc__range=[start_of_year, end_of_year],
            date_doc__isnull=False
        ).order_by('id')
    
    
class Financial(models.Model):
    name = models.CharField(max_length=255, blank=True, default="بدون نام")
    code = models.PositiveIntegerField(null=True, blank=True)
    date_doc = models.DateTimeField(blank=True, null=True, db_index=True)
    CostType = models.CharField(max_length=255, blank=True, null=True)
    descr = models.TextField(blank=True, null=True)
    fin_state = models.IntegerField(choices=[(e.value, e.name) for e in fin_state], default=fin_state.start.value)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)    
    tax = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='financials', null=True)
    Payment_type = models.BooleanField(default=False, blank=True)
    
    class Meta:
        verbose_name = "لیست اسناد تدارکات"
        verbose_name_plural = "لیست اسناد تدارکات"

    def __str__(self):
        return self.name    
    
    # Jalali date properties
    @property
    def date_doc_jalali(self):
        return to_jalali(self.date_doc)

    @property
    def created_jalali(self):
        return to_jalali(self.created)

    @property
    def updated_jalali(self):
        return to_jalali(self.updated)
    
    def delete(self, *args, **kwargs):
        """Override delete to prevent renumbering of other financials"""
        # First save the code and year information
        code = self.code
        jalali_year = JalaliDatetime(self.date_doc).year if self.date_doc else None
        
        # Perform the actual deletion
        super().delete(*args, **kwargs)
        
        # No need to update other financials - their codes remain as is
        
    @classmethod
    def get_financials_by_year(cls, year):
        """Get all financials for a specific Jalali year"""
        start_of_year = JalaliDatetime(year, 1, 1).todate()
        end_of_year = JalaliDatetime(year, 12, 29).todate()
        
        return cls.objects.filter(
            date_doc__range=[start_of_year, end_of_year],
            date_doc__isnull=False
        ).order_by('code')
   

class Contract(models.Model):
    name = models.CharField(max_length=255)
    code = models.PositiveIntegerField(null=True, blank=True)    
    Contractor = models.CharField(max_length=255, null=True)
    Contractor_id = models.CharField(max_length=255, null=True)
    Contractor_level = models.CharField(null=True, max_length=2)
    Contractor_type = models.ForeignKey(Contractor_type, on_delete=models.SET_NULL, related_name='contracts', null=True)
    # Contract_record = models.ManyToManyField(Contract_record, related_name='contracts')
    contract_number = models.CharField(max_length=255, null=True)
    document_date = models.DateTimeField(null=True)
    total_contract_amount = models.FloatField(null=True)
    Location = models.ForeignKey(sub_unit, on_delete=models.SET_NULL, related_name='contracts', null=True)
    descr = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    uploads = models.ManyToManyField(LogisticsUploads, blank=True)
    account_number = models.CharField(max_length=255, null=True)
    account_name = models.CharField(max_length=255, null=True)
    bank_name = models.CharField(max_length=255, null=True, verbose_name="نام بانک")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='contracts', null=True)
    program = models.ForeignKey(program, on_delete=models.SET_NULL, related_name='contracts', null=True)
    budget_row = models.ForeignKey(budget_row, on_delete=models.SET_NULL, related_name='contracts', null=True)
    cost_type = models.IntegerField(null=True)
    class Meta:
        verbose_name = "لیست قرارداد"
        verbose_name_plural = "لیست قرارداد"        
    
    def __str__(self) -> str:
        return self.name    
    
    # Jalali date properties
    @property
    def document_date_jalali(self):
        return to_jalali(self.document_date)

    @property
    def created_jalali(self):
        return to_jalali(self.created)

    @property
    def updated_jalali(self):
        return to_jalali(self.updated)
    
    def delete(self, *args, **kwargs):
        """Override delete to prevent renumbering of other contracts"""
        # First save the code and year information
        code = self.code
        jalali_year = JalaliDatetime(self.document_date).year if self.document_date else None
        
        # Perform the actual deletion
        super().delete(*args, **kwargs)
        
        # No need to update other contracts - their codes remain as is
        
    @classmethod
    def get_contracts_by_year(cls, year):
        """Get all contracts for a specific Jalali year"""
        start_of_year = JalaliDatetime(year, 1, 1).todate()
        end_of_year = JalaliDatetime(year, 12, 29).todate()
        
        return cls.objects.filter(
            document_date__range=[start_of_year, end_of_year],
            document_date__isnull=False
        ).order_by('code')
        

class Sign(models.Model):
    ROLE_CHOICES = [
        ('president', 'رئیس دانشگاه'),
        ('director', 'معاون اداری، عمرانی و مالی'),
        ('manager', 'مدیر منابع انسانی، اداری و پشتیبانی'),
        ('financialManager', 'مدیر امور مالی'),
        ('financialAssistant', 'صدور حواله'),
    ]
    name = models.CharField(max_length=255, blank=True, verbose_name="نام")
    last_name = models.CharField(max_length=255, blank=True, verbose_name="نام خانوادگی")  
    role = models.CharField(max_length=255, choices=ROLE_CHOICES, blank=True, verbose_name="سمت")      
    date_start = models.CharField(max_length=255, blank=True, null=True, verbose_name="تاریخ شروع")
    date_end = models.CharField(max_length=255, blank=True, null=True, verbose_name="تاریخ پایان")
    created = models.DateTimeField(auto_now_add=True, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)
    
    class Meta:
        verbose_name = "لیست امضا"
        verbose_name_plural = "لیست امضا"
      
    
    def __str__(self) -> str:
        return self.name    
    
   