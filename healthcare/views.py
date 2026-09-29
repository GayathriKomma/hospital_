from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Doctor, Patient, PatientDoctorMapping
from .serializers import (
    CustomTokenObtainPairSerializer,
    DoctorSerializer,
    MappingCreateSerializer,
    MappingReadSerializer,
    PatientSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DoctorViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    queryset = Doctor.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MappingCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mappings = PatientDoctorMapping.objects.filter(
            patient__created_by=request.user
        ).select_related("patient", "doctor")
        return Response(MappingReadSerializer(mappings, many=True).data)

    def post(self, request):
        serializer = MappingCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        mapping = serializer.save()
        return Response(
            MappingReadSerializer(mapping).data,
            status=status.HTTP_201_CREATED,
        )


class MappingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, identifier):
        mappings = PatientDoctorMapping.objects.filter(
            patient_id=identifier,
            patient__created_by=request.user,
        ).select_related("patient", "doctor")
        return Response(MappingReadSerializer(mappings, many=True).data)

    def delete(self, request, identifier):
        mapping = get_object_or_404(
            PatientDoctorMapping,
            pk=identifier,
            patient__created_by=request.user,
        )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
