from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from healthcare.views import (
    CustomTokenObtainPairView,
    DoctorViewSet,
    MappingCollectionView,
    MappingDetailView,
    PatientViewSet,
    RegisterView,
)

router = DefaultRouter()
router.register("patients", PatientViewSet, basename="patient")
router.register("doctors", DoctorViewSet, basename="doctor")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/mappings/", MappingCollectionView.as_view(), name="mapping-list-create"),
    path(
        "api/mappings/<int:identifier>/",
        MappingDetailView.as_view(),
        name="mapping-detail",
    ),
    path("api/", include(router.urls)),
]
