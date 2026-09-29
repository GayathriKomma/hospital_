from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Doctor, Patient, PatientDoctorMapping, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "name", "email", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "name": self.user.name,
            "email": self.user.email,
        }
        return data


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            "id",
            "name",
            "age",
            "gender",
            "email",
            "phone",
            "address",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = (
            "id",
            "name",
            "specialization",
            "email",
            "phone",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class MappingSerializer(serializers.ModelSerializer):
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(), source="patient"
    )
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(), source="doctor"
    )

    class Meta:
        model = PatientDoctorMapping
        fields = ("id", "patient_id", "doctor_id", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_patient_id(self, patient):
        if patient.created_by_id != self.context["request"].user.id:
            raise serializers.ValidationError("You do not have access to this patient.")
        return patient

    def validate(self, attrs):
        patient = attrs.get(
            "patient",
            self.instance.patient if self.instance is not None else None,
        )
        doctor = attrs.get(
            "doctor",
            self.instance.doctor if self.instance is not None else None,
        )
        duplicate = PatientDoctorMapping.objects.filter(
            patient=patient,
            doctor=doctor,
        )
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError(
                {"doctor_id": "This doctor is already assigned to this patient."}
            )
        return attrs
