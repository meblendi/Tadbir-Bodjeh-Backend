import django.contrib.auth.models
import django.db.models
from rest_framework import serializers

import tadbirbodjeh.models
from tadbirbodjeh.models import budget_chapter, budget_section, budget_row, program
from tadbirbodjeh.models import organization, unit
from .models import Financial, Logistics, LogisticsUploads, PettyCash, sub_unit, Sign


class sub_unitSerializer(serializers.ModelSerializer):
    unit_id = serializers.IntegerField(source='unit.id', read_only=True)
    organization_id = serializers.IntegerField(source='unit.organization.id', read_only=True)
    organization_name = serializers.CharField(source='unit.organization.name', read_only=True)
    class Meta:
        model = sub_unit
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.unit:
            representation['unit_id'] = instance.unit.id
            if instance.unit.organization:
                representation['organization_id'] = instance.unit.organization.id
        return representation


class pettyCashCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PettyCash
        fields = '__all__'


class pettyCashListSerializer(serializers.ModelSerializer):
    forwhom = serializers.SerializerMethodField()

    def get_forwhom(self, obj):
        user = obj.forwhom
        if user:
            return {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
            }
        return None

    # forhome
    class Meta:
        model = PettyCash
        fields = '__all__'
        # exclude = ['created_by']


class LogisticsUploadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticsUploads
        exclude = ['created_by']

class LogisticsUploadsSerializerforlist(serializers.ModelSerializer):
    class Meta:
        model = LogisticsUploads
        fields = ['name', 'file', 'id']
        
        
class LogisticsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        return obj.created_by.first_name + ' ' + obj.created_by.last_name
        
    class Meta:
        model = Logistics
        exclude = ['created_by']


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change endpoints.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class unitSerializer(serializers.ModelSerializer):
    sub_unit = sub_unitSerializer(many=True, read_only=True)

    class Meta:
        model = unit
        fields = '__all__'


class organizationSerializer(serializers.ModelSerializer):
    unit = unitSerializer(many=True, read_only=True)

    class Meta:
        model = organization
        fields = '__all__'


class BudgetRowSerializer(serializers.ModelSerializer):    

    class Meta:
        model = budget_row
        fields = '__all__'


class BudgetSectionSerializer(serializers.ModelSerializer):
    budget_row = BudgetRowSerializer(many=True, read_only=True)

    class Meta:
        model = budget_section
        fields = '__all__'


class BudgetChapterSerializer(serializers.ModelSerializer):
    budget_section = BudgetSectionSerializer(many=True, read_only=True)

    class Meta:
        model = budget_chapter
        fields = '__all__'


class programSerializer(serializers.ModelSerializer):
    class Meta:
        model = program
        fields = '__all__'


class NameIdSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'code']


class NameIdSerializerForProgramAndBudget(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'name', 'code', 'fin_code']


class BudgetRowNameIdSerializer(NameIdSerializerForProgramAndBudget):
    class Meta(NameIdSerializerForProgramAndBudget.Meta):
        model = budget_row


class SubUnitNameIdSerializer(NameIdSerializer):
    class Meta(NameIdSerializer.Meta):
        model = sub_unit


class ProgramNameIdSerializer(NameIdSerializerForProgramAndBudget):
    class Meta(NameIdSerializerForProgramAndBudget.Meta):
        model = program


class relationReadSerializer(serializers.ModelSerializer):
    budget_row = BudgetRowNameIdSerializer()
    organization = SubUnitNameIdSerializer(many=True)
    programs = ProgramNameIdSerializer(many=True)

    class Meta:
        model = tadbirbodjeh.models.relation
        fields = '__all__'
        
class relationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = tadbirbodjeh.models.relation
        fields = '__all__'
        


class FinancialSerializer(serializers.ModelSerializer):
    total_logistics_price = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    user_group = serializers.SerializerMethodField()

    def get_user_group(self, obj):
        if obj.created_by is None:
            return 'Unknown'
        else:
            group = obj.created_by.groups.first().name
            if group is None:
                return 'Unknown'
            else:
                return group

    def get_user(self, obj):
        first_name = obj.created_by.first_name if obj.created_by and obj.created_by.first_name else ''
        last_name = obj.created_by.last_name if obj.created_by and obj.created_by.last_name else ''
        return f"{first_name} {last_name}".strip()

    def get_total_logistics_price(self, obj):
        return obj.logistics.aggregate(django.db.models.Sum('price'))['price__sum'] or 0

    class Meta:
        model = Financial
        # fields = '__all__'
        exclude = ['created_by']
   

class ContractSerializer(serializers.ModelSerializer):
    paid_amount = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    contractor_type_name = serializers.CharField(source="Contractor_type.name", read_only=True) # New changes

    def get_user(self, obj):
        first_name = obj.created_by.first_name if obj.created_by and obj.created_by.first_name else ''
        last_name = obj.created_by.last_name if obj.created_by and obj.created_by.last_name else ''
        return f"{first_name} {last_name}".strip()
    def get_paid_amount(self, obj):
        import django.db.models
        return tadbirbodjeh.models.Contract_record.objects.filter(
            Contract=obj
        ).aggregate(
            total_paid=django.db.models.Sum('final_payable_amount')
        )['total_paid'] or 0

    class Meta:
        model = tadbirbodjeh.models.Contract
        fields = '__all__'
        extra_fields = ['contractor_type_name'] # New changes 


class Contractor_type_Serializer(serializers.ModelSerializer):

    class Meta:
        model = tadbirbodjeh.models.Contractor_type
        fields = '__all__'


class ContractRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = tadbirbodjeh.models.Contract_record
        fields = '__all__'


class LogisticsSerializerlist(serializers.ModelSerializer):
    uploads = LogisticsUploadsSerializerforlist(many=True, read_only=True)
    user = serializers.SerializerMethodField()
    Location = sub_unitSerializer()
    program = serializers.SerializerMethodField()
    budget_row = serializers.SerializerMethodField()
    Fdoc_key = FinancialSerializer()

    
    def get_user(self, obj):
        if obj.created_by is not None:
            return obj.created_by.first_name + ' ' + obj.created_by.last_name
        else:
            return 'Unknown User'

    def get_program(self, obj):
        from tadbirbodjeh.serializers import ProgramNameIdSerializer
        return ProgramNameIdSerializer(obj.program).data

    def get_budget_row(self, obj):
        from tadbirbodjeh.serializers import BudgetRowNameIdSerializer
        return BudgetRowNameIdSerializer(obj.budget_row).data

    class Meta:
        model = Logistics
        exclude = ['created_by']
        

class SignSerializer(serializers.ModelSerializer):    

    class Meta:
        model = Sign
        fields = '__all__'
