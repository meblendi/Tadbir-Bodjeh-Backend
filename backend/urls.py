"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

import tadbirbodjeh.models
from tadbirbodjeh.views import (
    FinancialViewSet,
    LogisticsViewSet,
    PasswordResetView,
    LogisticsUploadsViewSet, LogoutView, pettyCashViewSet, pettyCashReport, get_user_info, getAllLogisticUser,
    changeOwnerFinancial, OrganizationViewSet, UnitViewSet, SubUnitViewSet, SignViewSet
)
from tadbirbodjeh.views import GenerateExcelView

router = routers.DefaultRouter()
router.register(r"logistics", LogisticsViewSet, basename="logistics")
router.register(r"financial", FinancialViewSet)
router.register(r"logistics-uploads", LogisticsUploadsViewSet)
router.register(r"pettycash", pettyCashViewSet)
#################
# برای‌ استفاده در ایجاد مدرک بدون پیجنشن
# router.register(r"units", units)
################
router.register(r"organization", OrganizationViewSet)
router.register(r"unit", UnitViewSet)
router.register(r"subUnit", SubUnitViewSet)
router.register(r"budget_chapter", tadbirbodjeh.views.BudgetChapterViewSet)
router.register(r"budget_section", tadbirbodjeh.views.BudgetSectionViewSet)
router.register(r"budget_row", tadbirbodjeh.views.BudgetRowViewSet)

router.register(r"sign", SignViewSet)

router.register(r"program", tadbirbodjeh.views.programViewSet)
router.register(r"relation", tadbirbodjeh.views.relationViewSet)
router.register(r"contract", tadbirbodjeh.views.ContractView)
router.register(r"contractor_type", tadbirbodjeh.views.Contractor_type_View)
router.register(r"contract_record", tadbirbodjeh.views.ContractRecordViewSet)

# router.register(r"password-reset", PasswordResetView.as_view())
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/password-reset/", PasswordResetView.as_view()),
    path("api/getAllLogisticUser/", getAllLogisticUser.as_view()),
    path("api/changeOwnerFinancial/", changeOwnerFinancial.as_view()),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("auth/logout/", LogoutView.as_view()),
    path("mehdi/", tadbirbodjeh.views.index),
    path("group/", tadbirbodjeh.views.cheekGroupOfUser.as_view()),
    path("api/pettycashreport/", pettyCashReport.as_view(), name='ActiveReports'),
    path('get_user_info/', get_user_info.as_view(), name='get_user_info'),
    path('api-auth/', include('rest_framework.urls')),  # Include Django REST Framework URLs
    path('api/generate-excel/<int:financial_id>/', GenerateExcelView.as_view(), name='generate-excel'),
    # path("accounts/", include("django.contrib.auth.urls")),
]