import datetime
import logging
from io import BytesIO

import django.contrib.auth
import django.contrib.auth.decorators
import django.contrib.auth.mixins
import django.contrib.auth.models
import django.core.exceptions
import django.db.models
import django.http
import django.shortcuts
import django.utils.dateparse
import rest_framework.generics
import rest_framework.permissions
import rest_framework.views
import rest_framework_simplejwt.exceptions
import rest_framework_simplejwt.tokens
import xlsxwriter
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import permissions, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import tadbirbodjeh.serializers
from tadbirbodjeh.models import organization, unit, budget_chapter, budget_section, budget_row, program, \
    relation, Contract, Contractor_type, Contract_record
from tadbirbodjeh.serializers import organizationSerializer, unitSerializer, BudgetRowSerializer, \
    BudgetSectionSerializer, BudgetChapterSerializer, programSerializer, relationReadSerializer, relationWriteSerializer
from .models import Financial, Logistics, LogisticsUploads, PettyCash, sub_unit, Sign
from .serializers import (
    FinancialSerializer, SignSerializer,
    LogisticsSerializer,
    LogisticsUploadsSerializer, LogisticsSerializerlist, sub_unitSerializer,
    PasswordChangeSerializer, pettyCashListSerializer, pettyCashCreateSerializer,
)

logger = logging.getLogger(__name__)


class CustomObjectPermissions(permissions.DjangoModelPermissions):
    """
    Similar to `DjangoObjectPermissions`, but adding 'view' permissions.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }                


class pettyCashViewSet(viewsets.ModelViewSet):
    queryset = PettyCash.objects.all().reverse().order_by('id')
    # user_filter_backends = [filters.ObjectPermissionsFilter]
    permission_classes = [CustomObjectPermissions]

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        if any(name.startswith("logistics") for name in group_names):
            if 'L_conf' in request.data and len(request.data) == 1:

                instance.L_conf = request.data['L_conf']
                instance.save()
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            else:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_400_BAD_REQUEST)

        elif any(name.startswith("financial") for name in group_names):
            if 'F_conf' in request.data and len(request.data) == 1:
                instance.F_conf = request.data['F_conf']
                instance.save()
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            else:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        if instance.L_conf == True and instance.F_conf is None:
            if any(name.startswith("logistics") for name in group_names):
                return super().update(request, *args, **kwargs)
            else:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_403_FORBIDDEN)
        elif instance.L_conf is None and instance.F_conf == True:
            if any(name.startswith("financial") for name in group_names):
                return super().update(request, *args, **kwargs)
            else:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"error": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return pettyCashCreateSerializer
        return pettyCashListSerializer

    def perform_create(self, serializer):
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        if any(name.startswith("logistics") for name in group_names) and not self.request.user.is_staff:
            instance = serializer.save(forwhom=self.request.user, created_by=self.request.user)
            return
        instance = serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = self.queryset
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        get_nulls = self.request.query_params.get('get_nulls', None)
        if get_nulls is not None and any(name.startswith("logistics") for name in group_names):
            queryset = queryset.filter(L_conf__isnull=True).filter(forwhom=self.request.user)
        if get_nulls is not None and any(name.startswith("financial") for name in group_names):
            queryset = queryset.filter(F_conf__isnull=True)
        if self.request.user.is_staff or any(name.startswith("financial") for name in group_names):
            return queryset
        return queryset.filter(forwhom=self.request.user)


# create  view that report all PettyCash and Financial between two date in query params by date_doc filed
class pettyCashReport(rest_framework.views.APIView):
    def post(self, request, format=None):
        start_date_str = request.data.get('start_date', None)
        end_date_str = request.data.get('end_date', None)
        user_id = request.data.get('user', None)
        print(user_id)
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]

        if start_date_str and end_date_str:
            start_date = django.utils.dateparse.parse_datetime(start_date_str)
            end_date = django.utils.dateparse.parse_datetime(end_date_str)
            if request.user.is_staff or any(name.startswith("financial") for name in group_names):
                petty_cash_objects = PettyCash.objects.filter(date_doc__range=[start_date, end_date],
                                                              forwhom__id=user_id, L_conf=True, F_conf=True)
                financial_objects = Financial.objects.filter(date_doc__range=[start_date, end_date],
                                                             created_by__id=user_id)
            else:
                petty_cash_objects = PettyCash.objects.filter(date_doc__range=[start_date, end_date],
                                                              forwhom=request.user, L_conf=True, F_conf=True)
                financial_objects = Financial.objects.filter(date_doc__range=[start_date, end_date],
                                                             created_by=request.user)
            
            petty_cash_total_price = petty_cash_objects.aggregate(django.db.models.Sum('price'))['price__sum']
            grouped_by_payment_type = [True, False]
            results = []
            for group in grouped_by_payment_type:
                financial_objects_payment_type = financial_objects.filter(Payment_type=group)
                grouped_by_fin_state = financial_objects_payment_type.values('fin_state').annotate(
                    total_price=django.db.models.Sum('logistics__price'))
                results.append({
                    'Payment_type': group,
                    'fin_state_groups': list(grouped_by_fin_state)
                })
            
            return Response({
                'petty_cash': petty_cash_total_price,
                'aggregated_financials': list(results)
            })

        return Response({"error": "start_date and end_date are required in the request body"}, status=400)


# return user group name and id
from django.db import models
from rest_framework.decorators import action

class LogisticsViewSet(viewsets.ModelViewSet):
    permission_classes = [CustomObjectPermissions]
    

    def get_queryset(self):
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        Fdoc_key = self.request.query_params.get('Fdoc_key', None)
        get_nulls = self.request.query_params.get('get_nulls', None)
        search = self.request.query_params.get('search', None)
        year = self.request.query_params.get('date_doc_jalali_year', None)
        fin_state = self.request.query_params.get('Fdoc_key__fin_state', None)        
        logistics_type = self.request.query_params.get('type', None)
        organization_id = self.request.query_params.get('Location__unit__organization', None)
        unit_id = self.request.query_params.get('Location__unit', None)
        location_id = self.request.query_params.get('Location', None)        
        
        queryset = Logistics.objects.all()
        
        if year:
            try:
                start_of_year = JalaliDatetime(int(year), 1, 1).todate()
                end_of_year = JalaliDatetime(int(year), 12, 29).todate()
                queryset = queryset.filter(date_doc__range=[start_of_year, end_of_year])
            except ValueError:
                pass        
        
        if fin_state in ['2', '1', '0']:
            queryset = queryset.filter(Fdoc_key__fin_state=fin_state)
            
        if logistics_type in ['True', 'False']:
            queryset = queryset.filter(type=logistics_type)
        
        if organization_id:
            queryset = queryset.filter(Location__unit__organization=organization_id)
        
        if unit_id:
            queryset = queryset.filter(Location__unit=unit_id)
            
        if location_id:
            queryset = queryset.filter(Location_id=location_id)
            
    
        if get_nulls is not None:
            if search is not None:
                if self.request.user.is_staff:
                    return queryset.filter(Fdoc_key__isnull=True).filter(
                        Q(name__icontains=search) | Q(id__icontains=search)).reverse().order_by('id')
                return queryset.filter(Fdoc_key__isnull=True).filter(
                    Q(name__icontains=search) | Q(id__icontains=search)).reverse().order_by('id').filter(
                    created_by=self.request.user)
            if get_nulls == 'true':
                if self.request.user.is_staff:
                    return queryset.filter(Fdoc_key__isnull=True).reverse().order_by('id')
                return queryset.filter(Fdoc_key__isnull=True).reverse().order_by('id').filter(
                    created_by=self.request.user)
            elif get_nulls == 'false':
                if self.request.user.is_staff:
                    return queryset.filter(Fdoc_key__isnull=False).reverse().order_by('id')
                return queryset.filter(Fdoc_key__isnull=False).reverse().order_by('id').filter(
                    created_by=self.request.user)
        elif Fdoc_key is not None:
            if self.request.user.is_staff or any(name.startswith("financial") for name in group_names):
                return queryset.filter(Q(Fdoc_key__exact=Fdoc_key)).order_by('id')
            return queryset.filter(Q(Fdoc_key__exact=Fdoc_key)).order_by('id').filter(
                created_by=self.request.user)
        else:
            if self.request.user.is_staff or any(name.startswith("financial") for name in group_names):
                return queryset.all().reverse().order_by('id')
            return queryset.all().reverse().order_by('id').filter(created_by=self.request.user)
        
    @action(detail=False, methods=['get'])
    def total_price(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Calculate total price
        total = queryset.aggregate(total_price=models.Sum('price'))['total_price'] or 0
        
        return Response({'total_price': total})
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        if instance.Fdoc_key is not None:
            if any(name.startswith("financial") for name in group_names) and instance.Fdoc_key.fin_state > 2:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_403_FORBIDDEN)
            if any(name.startswith("logistic") for name in group_names) and instance.Fdoc_key.fin_state > 1:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        if instance.Fdoc_key is not None:
            if any(name.startswith("financial") for name in group_names) and instance.Fdoc_key.fin_state > 2:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_403_FORBIDDEN)

            if any(name.startswith("logistic") for name in group_names) and instance.Fdoc_key.fin_state > 1:
                return Response({"error": "You do not have permission to perform this action."},
                                status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)

    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.Fdoc_key:
            return Response({"error": "This object is related to a financial document"}, status=400)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LogisticsSerializerlist
        return LogisticsSerializer


class LogisticsUploadsViewSet(viewsets.ModelViewSet):
    queryset = LogisticsUploads.objects.all()
    serializer_class = LogisticsUploadsSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    # user_filter_backends = [filters.ObjectPermissionsFilter]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        upload = self.get_object()
        # delete the file before the object
        upload.file.delete()
        try:
            instance = self.get_object()
            self.perform_destroy(instance)

        except django.http.Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(rest_framework.views.APIView):
    permission_classes = (rest_framework.permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = rest_framework_simplejwt.tokens.RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_200_OK)
        except (django.core.exceptions.ObjectDoesNotExist, rest_framework_simplejwt.exceptions.TokenError):
            return Response(status=status.HTTP_400_BAD_REQUEST)



class get_user_info(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        return django.http.JsonResponse({
            'username': user.username,
            'email': user.email,
            'name': user.first_name + ' ' + user.last_name,
            'admin': user.is_staff,
            # add any other user fields you are interested in
        })


class cheekGroupOfUser(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        group = user.groups.first()
        if group:
            return Response(group.name)
        else:
            return Response('None')



class changeOwnerFinancial(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.IsAdminUser]

    def post(self, request, format=None):
        fin_id = request.data.get('fin_id', None)
        new_user_id = request.data.get('new_user_id', None)
        if fin_id and new_user_id:
            f_doc = django.shortcuts.get_object_or_404(Financial, id=fin_id)
            if f_doc.fin_state == 0:
                f_doc.created_by_id = new_user_id
                f_doc.save()
                for logistics_entry in f_doc.logistics.all():
                    logistics_entry.created_by_id = new_user_id
                    logistics_entry.save()
                return Response("success", status=200)
            else:
                return Response({"error": "fin_state"}, status=400)

        else:
            return Response({"error": "Invalid data"}, status=400)


class getAllLogisticUser(rest_framework.views.APIView):
    permission_classes = [rest_framework.permissions.IsAuthenticated]

    # get All  User of groupOfUser that starts with "Logistics"
    def get(self, request, format=None):
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        if self.request.user.is_staff or any(name.startswith("financial") for name in group_names):
            # Get all groups whose names start with "Logistics"
            logistic_groups = django.contrib.auth.models.Group.objects.filter(name__startswith="logistics")

            # Get all users belonging to these groups
            logistic_users = django.contrib.auth.models.User.objects.filter(groups__in=logistic_groups).distinct()
            # for user in logistic_users:
            #     print(user.id)
            user_data = [
                {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                }
                for user in logistic_users
            ]
            return Response(user_data, status=status.HTTP_200_OK)
        else:
            return Response("You are not authorized to view this data", status=status.HTTP_403_FORBIDDEN)


def index(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return django.http.HttpResponse(html, status=403)


class PasswordResetView(rest_framework.generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """

    serializer_class = PasswordChangeSerializer
    model = django.contrib.auth.models.User
    permission_classes = (rest_framework.permissions.IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            django.contrib.auth.update_session_auth_hash(request, self.object)  # Important!
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# write view for organization,unit,sub_unit model
from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 15  # Default page size
    page_size_query_param = 'page_size'  # Allows client to override
    max_page_size = 100  # Maximum limit

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = organization.objects.all().prefetch_related('unit')
    serializer_class = organizationSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]
    pagination_class = CustomPagination  # Use custom pagination

    def get_queryset(self):
        queryset = organization.objects.all().prefetch_related('unit')
        no_pagination = self.request.query_params.get('no_pagination', None)
        year = self.request.query_params.get('year', None)
        
        if no_pagination == 'true' and year:
            queryset = queryset.filter(year=year)
            self.pagination_class = None
        if no_pagination == 'true':
            self.pagination_class = None
        if year:
            queryset = queryset.filter(year=year)
        return queryset


class UnitViewSet(viewsets.ModelViewSet):
    queryset = unit.objects.all().prefetch_related('sub_unit')
    serializer_class = unitSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_queryset(self):
        queryset = unit.objects.all()
        no_pagination = self.request.query_params.get('no_pagination', None)
        year = self.request.query_params.get('year', None)
        organization_id = self.request.query_params.get('organization', None)
        
        if no_pagination == 'true' and year:
            queryset = queryset.filter(year=year)
            self.pagination_class = None
        if no_pagination == 'true':
            self.pagination_class = None
        if year:
            queryset = queryset.filter(year=year)
        if organization_id:
            queryset = queryset.filter(organization=organization_id)
            
        return queryset


class SubUnitViewSet(viewsets.ModelViewSet):
    queryset = sub_unit.objects.all()
    serializer_class = sub_unitSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_queryset(self):
        queryset = sub_unit.objects.all()
        no_pagination = self.request.query_params.get('no_pagination', None)
        year = self.request.query_params.get('year', None)
        organization_id = self.request.query_params.get('unit__organization', None)
        unit_id = self.request.query_params.get('unit', None)        
        
        if no_pagination == 'true' and year:
            queryset = queryset.filter(year=year)
            self.pagination_class = None
        if no_pagination == 'true':
            self.pagination_class = None
        if year:
            queryset = queryset.filter(year=year)
        if organization_id:
            queryset = queryset.filter(unit__organization=organization_id)
        if unit_id:
            queryset = queryset.filter(unit=unit_id)
            
        return queryset


class BudgetChapterViewSet(viewsets.ModelViewSet):
    queryset = budget_chapter.objects.all()
    serializer_class = BudgetChapterSerializer
    permission_classes = [IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_queryset(self):
        queryset = budget_chapter.objects.all()
        no_pagination = self.request.query_params.get('no_pagination', None)
        year = self.request.query_params.get('year', None)
        if no_pagination == 'true' and year:
            queryset = queryset.filter(year=year)
            self.pagination_class = None
        if no_pagination == 'true':
            self.pagination_class = None
        if year:
            queryset = queryset.filter(year=year)
        return queryset


class BudgetSectionViewSet(viewsets.ModelViewSet):
    queryset = budget_section.objects.all()
    serializer_class = BudgetSectionSerializer
    permission_classes = [IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_queryset(self):
        queryset = budget_section.objects.all()
        no_pagination = self.request.query_params.get('no_pagination', None)
        year = self.request.query_params.get('year', None)
        if no_pagination == 'true' and year:
            queryset = queryset.filter(year=year)
            self.pagination_class = None
        if no_pagination == 'true':
            self.pagination_class = None
        if year:
            queryset = queryset.filter(year=year)
        return queryset


class BudgetRowViewSet(viewsets.ModelViewSet):
    queryset = budget_row.objects.all()
    serializer_class = BudgetRowSerializer
    permission_classes = [IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_queryset(self):
        queryset = budget_row.objects.all()
        no_pagination = self.request.query_params.get('no_pagination', None)
        year = self.request.query_params.get('year', None)
        if no_pagination == 'true' and year:
            queryset = queryset.filter(year=year)
            self.pagination_class = None
        if no_pagination == 'true':
            self.pagination_class = None
        if year:
            queryset = queryset.filter(year=year)
        return queryset


class programViewSet(viewsets.ModelViewSet):
    queryset = program.objects.all()
    serializer_class = programSerializer
    permission_classes = [IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_serializer_class(self):
        return programSerializer  # or swap with another if needed

    def get_queryset(self):
        queryset = program.objects.all()
        no_pagination = self.request.query_params.get('no_pagination')
        year = self.request.query_params.get('year')

        if year:
            queryset = queryset.filter(year=year)
        if no_pagination == 'true':
            self.pagination_class = None

        return queryset



class relationViewSet(viewsets.ModelViewSet):
    queryset = relation.objects.all()
    permission_classes = [IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return relationWriteSerializer
        return relationReadSerializer

    def get_queryset(self):
        queryset = relation.objects.all()
        no_pagination = self.request.query_params.get('no_pagination')
        organization_id = self.request.query_params.get('organization')
        year = self.request.query_params.get('year')

        if year:
            queryset = queryset.filter(year=year)
        if organization_id:
            queryset = queryset.filter(organization__id=organization_id)
        if no_pagination == 'true':
            self.pagination_class = None

        return queryset




class GenerateExcelView(rest_framework.views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, financial_id):
        try:
            financial = Financial.objects.get(id=financial_id)

            if not financial.Payment_type:
                return Response({"error": "Payment_type is not true for this Financial record"},
                                status=status.HTTP_400_BAD_REQUEST)

            logistics = Logistics.objects.filter(Fdoc_key=financial)

            # Group by account_number and account_name, sum the prices
            grouped_logistics = logistics.values('account_number', 'account_name', 'bank_name').annotate(
                total_price=Sum('price'))

            # Create a workbook and add a worksheet.
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('ACHGroupTransfer')

            # Add headers
            headers = ['Amount', 'CreditIBAN', 'CurrencyCode', 'CreditAccountOwnerName', 'CreditAccountOwnerIdentifier',
                       'Identifier', 'Description']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)

            # Add data
            for row, item in enumerate(grouped_logistics, start=1):
                worksheet.write(row, 0, item['total_price'])
                worksheet.write(row, 1, f"IR{item['account_number']}")
                worksheet.write(row, 2, '')  # CurrencyCode (empty)
                worksheet.write(row, 3, item['account_name'])
                worksheet.write(row, 4, '')  # CreditAccountOwnerIdentifier (empty)
                worksheet.write(row, 5, '')  # Identifier (empty)
                worksheet.write(row, 6, '')  # Description (empty)

            workbook.close()

            # Create the HttpResponse object with Excel mime type
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename=financial_{financial_id}_logistics.xlsx'
            response.write(output.getvalue())

            return response

        except Financial.DoesNotExist:
            return Response({"error": "Financial record not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from khayyam import JalaliDatetime
from django.db.models import Max


class FinancialViewSet(viewsets.ModelViewSet):
    queryset = Financial.objects.all().reverse().order_by('id')
    serializer_class = FinancialSerializer    
    permission_classes = [CustomObjectPermissions]    

    def perform_create(self, serializer):
        # First validate and get the data
        validated_data = serializer.validated_data
        
        # Ensure date_doc is provided
        if not validated_data.get('date_doc'):
            raise ValueError("date_doc is required to generate code")

        # Get Jalali year from date_doc
        jalali_date = JalaliDatetime(validated_data['date_doc'])
        jalali_year = jalali_date.year

        # Get the start and end of the Jalali year in Gregorian
        start_of_year = JalaliDatetime(jalali_year, 1, 1).todate()
        end_of_year = JalaliDatetime(jalali_year, 12, 29).todate()

        # Get the max code for this year
        max_code = Financial.objects.filter(
            date_doc__range=[start_of_year, end_of_year],
            date_doc__isnull=False
        ).aggregate(Max('code'))['code__max'] or 0

        # Calculate the next code
        next_code = max_code + 1

        # Save with the calculated code
        serializer.save(
            code=next_code,
            created_by=self.request.user)

    
    def get_queryset(self):
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]
        fin_state = self.request.query_params.get('fin_state', None)
        year = self.request.query_params.get('date_doc_jalali_year', None)
        
        queryset = self.queryset
        
        if fin_state is not None:
            queryset = queryset.filter(fin_state=fin_state)
            
        if year:
            try:
                start_of_year = JalaliDatetime(int(year), 1, 1).todate()
                end_of_year = JalaliDatetime(int(year), 12, 29).todate()
                queryset = queryset.filter(date_doc__range=[start_of_year, end_of_year])
            except ValueError:
                pass

        if self.request.user.is_staff or any(name.startswith("financial") for name in group_names):
            return queryset
        return queryset.filter(created_by=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user_groups = self.request.user.groups.all()
        group_names = [group.name for group in user_groups]

        # Check if any group name starts with "Financial"
        if any(name.startswith("financial") for name in group_names):
            # Only allow updating the fin_state field
            if 'fin_state' in request.data:
                if instance.fin_state == 3:
                    return Response({"error": "cant changed from state final."},
                                    status=status.HTTP_400_BAD_REQUEST)
                instance.fin_state = request.data['fin_state']
                instance.save()
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            else:
                return Response({"error": "Only fin_state field can be updated in financial."},
                                status=status.HTTP_400_BAD_REQUEST)

        elif (name.startswith("logistics") for name in group_names):
            # allow updating the fin_state field only from 1.0 to 2
            if 'fin_state' in request.data:
                if instance.fin_state == 0 and request.data['fin_state'] == 1:
                    instance.fin_state = request.data['fin_state']
                    instance.save()
                    serializer = self.get_serializer(instance)
                    return Response(serializer.data)
                else:
                    return Response({"error": "Only fin_state field can be updated form 0 to 1 in logistics."},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                # save it with the same data
                return self.partial_update(request, *args, **kwargs)

        else:
            return Response({"error": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)


class ContractView(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = tadbirbodjeh.serializers.ContractSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['id', 'total_contract_amount', 'paid_amount', 'document_date']
    ordering = ['-id']  # Default ordering

    def perform_create(self, serializer):
        # First validate and get the data
        validated_data = serializer.validated_data
        
        # Ensure document_date is provided
        if not validated_data.get('document_date'):
            raise ValueError("document_date is required to generate code")

        # Get Jalali year from document_date
        jalali_date = JalaliDatetime(validated_data['document_date'])
        jalali_year = jalali_date.year

        # Get the start and end of the Jalali year in Gregorian
        start_of_year = JalaliDatetime(jalali_year, 1, 1).todate()
        end_of_year = JalaliDatetime(jalali_year, 12, 29).todate()

        # Get the max code for this year
        max_code = Contract.objects.filter(
            document_date__range=[start_of_year, end_of_year],
            document_date__isnull=False
        ).aggregate(Max('code'))['code__max'] or 0

        # Calculate the next code
        next_code = max_code + 1

        # Save with the calculated code
        serializer.save(
            code=next_code,
            created_by=self.request.user
        )
        

class Contractor_type_View(viewsets.ModelViewSet):
    queryset = Contractor_type.objects.all()
    serializer_class = tadbirbodjeh.serializers.Contractor_type_Serializer
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def get_queryset(self):
        queryset = Contractor_type.objects.all()
        no_pagination = self.request.query_params.get('no_pagination', None)
        contractor_level = self.request.query_params.get('contractor_level', None)
        if no_pagination == 'true':
            self.pagination_class = None
        if contractor_level:
            queryset = queryset.filter(Contractor_level=contractor_level)
        return queryset

class ContractRecordViewSet(viewsets.ModelViewSet):
    queryset = Contract_record.objects.all()
    serializer_class = tadbirbodjeh.serializers.ContractRecordSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]

    def perform_create(self, serializer):
        # get sum of prices of all  related logstics
        instance = serializer.save(created_by=self.request.user)
    def get_queryset(self):
        queryset = Contract_record.objects.all()
        no_pagination = self.request.query_params.get('no_pagination', None)
        contract = self.request.query_params.get('contract', None)
        if no_pagination == 'true':
            self.pagination_class = None
        if contract:
            queryset = queryset.filter(Contract=contract)
        return queryset
    

class SignViewSet(viewsets.ModelViewSet):    
    queryset = Sign.objects.all()
    serializer_class = SignSerializer
    permission_classes = [rest_framework.permissions.IsAuthenticated, rest_framework.permissions.DjangoModelPermissions]
