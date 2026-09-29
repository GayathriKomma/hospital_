from io import StringIO

from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Doctor, Patient, PatientDoctorMapping, User


class HealthcareApiTests(APITestCase):
    password = "Strong-test-pass-123!"

    def test_homepage_renders_the_ui(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Healthcare")
        self.assertContains(response, "Create account")

    def test_demo_seed_is_repeatable(self):
        call_command("seed_demo", stdout=StringIO())
        call_command("seed_demo", stdout=StringIO())

        user = User.objects.get(email="demo@healthcare.example")
        self.assertTrue(user.check_password("CareDemo#2026!"))
        self.assertEqual(Patient.objects.filter(created_by=user).count(), 3)
        self.assertEqual(Doctor.objects.count(), 3)
        self.assertEqual(PatientDoctorMapping.objects.count(), 4)

    def test_protected_routes_require_authentication(self):
        response = self.client.get("/api/patients/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def register(self, email):
        return self.client.post(
            "/api/auth/register/",
            {
                "name": "Test Owner",
                "email": email,
                "password": self.password,
            },
            format="json",
        )

    def authenticate(self, email):
        response = self.client.post(
            "/api/auth/login/",
            {"email": email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_register_login_and_patient_crud(self):
        registered = self.register("owner@example.com")
        self.assertEqual(registered.status_code, status.HTTP_201_CREATED)
        duplicate = self.register("owner@example.com")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        login = self.client.post(
            "/api/auth/login/",
            {"email": "owner@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)
        self.assertIn("refresh", login.data)
        self.assertEqual(login.data["user"]["email"], "owner@example.com")
        refreshed = self.client.post(
            "/api/auth/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
        )
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn("access", refreshed.data)

        self.authenticate("owner@example.com")
        created = self.client.post(
            "/api/patients/",
            {"name": "A Patient", "age": 30, "gender": "other"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        patient_id = created.data["id"]
        self.assertEqual(self.client.get("/api/patients/").data["count"], 1)
        self.assertEqual(
            self.client.get(f"/api/patients/{patient_id}/").data["id"],
            patient_id,
        )
        replaced = self.client.put(
            f"/api/patients/{patient_id}/",
            {
                "name": "Updated Patient",
                "age": 31,
                "gender": "other",
                "email": "patient@example.com",
                "phone": "555-0100",
                "address": "10 Main Street",
            },
            format="json",
        )
        self.assertEqual(replaced.status_code, status.HTTP_200_OK)
        self.assertEqual(replaced.data["name"], "Updated Patient")
        updated = self.client.patch(
            f"/api/patients/{patient_id}/",
            {"age": 32},
            format="json",
        )
        self.assertEqual(updated.data["age"], 32)
        self.assertEqual(
            self.client.delete(f"/api/patients/{patient_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(
            self.client.get(f"/api/patients/{patient_id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_patients_and_mappings_are_private_to_their_owner(self):
        owner = User.objects.create_user(
            email="owner@example.com",
            password=self.password,
            name="Patient Owner",
        )
        patient = Patient.objects.create(
            name="Private Patient",
            age=40,
            gender="female",
            created_by=owner,
        )
        doctor = Doctor.objects.create(
            name="A Doctor",
            specialization="Cardiology",
            created_by=owner,
        )
        self.assertEqual(
            self.register("other@example.com").status_code,
            status.HTTP_201_CREATED,
        )
        self.authenticate("other@example.com")
        self.assertEqual(self.client.get("/api/patients/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/patients/{patient.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        invalid_mapping = self.client.post(
            "/api/mappings/",
            {"patient_id": patient.id, "doctor_id": doctor.id},
            format="json",
        )
        self.assertEqual(
            invalid_mapping.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_doctor_crud_and_mapping(self):
        self.register("owner@example.com")
        self.authenticate("owner@example.com")
        patient = self.client.post(
            "/api/patients/",
            {"name": "A Patient", "age": 30, "gender": "other"},
            format="json",
        )
        doctor = self.client.post(
            "/api/doctors/",
            {"name": "A Doctor", "specialization": "Cardiology"},
            format="json",
        )
        self.assertEqual(doctor.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.get("/api/doctors/").data["count"], 1)
        doctor_id = doctor.data["id"]
        self.assertEqual(
            self.client.get(f"/api/doctors/{doctor_id}/").data["id"],
            doctor_id,
        )
        replaced_doctor = self.client.put(
            f"/api/doctors/{doctor_id}/",
            {
                "name": "Dr. Updated",
                "specialization": "Neurology",
                "email": "doctor@example.com",
                "phone": "555-0110",
            },
            format="json",
        )
        self.assertEqual(replaced_doctor.status_code, status.HTTP_200_OK)
        self.assertEqual(replaced_doctor.data["name"], "Dr. Updated")
        updated_doctor = self.client.patch(
            f"/api/doctors/{doctor_id}/",
            {"specialization": "Cardiology"},
            format="json",
        )
        self.assertEqual(updated_doctor.data["specialization"], "Cardiology")
        mapping = self.client.post(
            "/api/mappings/",
            {"patient_id": patient.data["id"], "doctor_id": doctor_id},
            format="json",
        )
        self.assertEqual(mapping.status_code, status.HTTP_201_CREATED)
        mapping_id = mapping.data["id"]
        self.assertEqual(self.client.get("/api/mappings/").data["count"], 1)
        self.assertEqual(
            self.client.get(f"/api/mappings/{mapping_id}/").data["id"],
            mapping_id,
        )
        replaced_mapping = self.client.put(
            f"/api/mappings/{mapping_id}/",
            {"patient_id": patient.data["id"], "doctor_id": doctor_id},
            format="json",
        )
        self.assertEqual(replaced_mapping.status_code, status.HTTP_200_OK)
        updated_mapping = self.client.patch(
            f"/api/mappings/{mapping_id}/",
            {"doctor_id": doctor_id},
            format="json",
        )
        self.assertEqual(updated_mapping.status_code, status.HTTP_200_OK)
        duplicate = self.client.post(
            "/api/mappings/",
            {"patient_id": patient.data["id"], "doctor_id": doctor_id},
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.delete(f"/api/mappings/{mapping_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(
            self.client.get(f"/api/mappings/{mapping_id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(f"/api/doctors/{doctor_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
