from rest_framework import status
from rest_framework.test import APITestCase

from .models import Patient, User


class HealthcareApiTests(APITestCase):
    def register(self, email="owner@example.com"):
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Test Owner",
                "email": email,
                "password": "Strong-test-pass-123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response

    def authenticate(self, email="owner@example.com"):
        response = self.client.post(
            "/api/auth/login/",
            {"email": email, "password": "Strong-test-pass-123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_register_login_and_authenticated_patient_crud(self):
        self.register()
        login = self.client.post(
            "/api/auth/login/",
            {"email": "owner@example.com", "password": "Strong-test-pass-123!"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)
        self.assertIn("refresh", login.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        created = self.client.post(
            "/api/patients/",
            {"name": "A Patient", "age": 30, "gender": "other"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        patient_id = created.data["id"]
        self.assertEqual(self.client.get("/api/patients/").data[0]["id"], patient_id)
        self.assertEqual(
            self.client.get(f"/api/patients/{patient_id}/").status_code,
            status.HTTP_200_OK,
        )
        updated = self.client.put(
            f"/api/patients/{patient_id}/",
            {"name": "Updated Patient", "age": 31, "gender": "other"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["name"], "Updated Patient")
        self.assertEqual(
            self.client.delete(f"/api/patients/{patient_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_patient_records_are_private_to_their_creator(self):
        self.register()
        owner = Patient.objects.create(
            name="Private Patient",
            age=40,
            gender="female",
            created_by=User.objects.get(email="owner@example.com"),
        )
        other = self.client.post(
            "/api/auth/register/",
            {
                "name": "Another User",
                "email": "other@example.com",
                "password": "Another-strong-pass-123!",
            },
            format="json",
        )
        self.assertEqual(other.status_code, status.HTTP_201_CREATED)
        login = self.client.post(
            "/api/auth/login/",
            {"email": "other@example.com", "password": "Another-strong-pass-123!"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(self.client.get("/api/patients/").data, [])
        self.assertEqual(
            self.client.get(f"/api/patients/{owner.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_doctor_crud_and_patient_doctor_mapping(self):
        self.register()
        self.authenticate()
        patient_response = self.client.post(
            "/api/patients/",
            {"name": "A Patient", "age": 30, "gender": "other"},
            format="json",
        )
        doctor_response = self.client.post(
            "/api/doctors/",
            {"name": "A Doctor", "specialization": "Cardiology"},
            format="json",
        )
        self.assertEqual(doctor_response.status_code, status.HTTP_201_CREATED)
        doctor_id = doctor_response.data["id"]
        self.assertEqual(self.client.get("/api/doctors/").status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get(f"/api/doctors/{doctor_id}/").status_code,
            status.HTTP_200_OK,
        )
        updated_doctor = self.client.patch(
            f"/api/doctors/{doctor_id}/",
            {"specialization": "Neurology"},
            format="json",
        )
        self.assertEqual(updated_doctor.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_doctor.data["specialization"], "Neurology")
        mapping_response = self.client.post(
            "/api/mappings/",
            {
                "patient_id": patient_response.data["id"],
                "doctor_id": doctor_id,
            },
            format="json",
        )
        self.assertEqual(mapping_response.status_code, status.HTTP_201_CREATED)
        mapping_id = mapping_response.data["id"]
        self.assertEqual(len(self.client.get("/api/mappings/").data), 1)
        self.assertEqual(
            len(
                self.client.get(
                    f"/api/mappings/{patient_response.data['id']}/"
                ).data
            ),
            1,
        )
        self.assertEqual(
            self.client.delete(f"/api/mappings/{mapping_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(
            self.client.delete(f"/api/doctors/{doctor_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_api_requires_authentication_and_duplicate_mapping_is_rejected(self):
        self.assertEqual(
            self.client.get("/api/patients/").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.register()
        self.authenticate()
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
        payload = {"patient_id": patient.data["id"], "doctor_id": doctor.data["id"]}
        self.assertEqual(
            self.client.post("/api/mappings/", payload, format="json").status_code,
            status.HTTP_201_CREATED,
        )
        duplicate = self.client.post("/api/mappings/", payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
