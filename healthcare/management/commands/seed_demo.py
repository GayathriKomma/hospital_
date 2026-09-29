from django.core.management.base import BaseCommand

from healthcare.models import Doctor, Patient, PatientDoctorMapping, User


class Command(BaseCommand):
    help = "Add sample healthcare records for local testing."

    demo_email = "demo@healthcare.example"
    demo_password = "CareDemo#2026!"

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email=self.demo_email,
            defaults={"name": "Demo User"},
        )
        if created:
            user.set_password(self.demo_password)
            user.save(update_fields=["password"])

        patients = [
            {
                "name": "Jordan Taylor",
                "age": 34,
                "gender": "other",
                "email": "jordan.taylor@example.test",
                "phone": "555-0101",
                "address": "10 Sample Street",
            },
            {
                "name": "Morgan Chen",
                "age": 52,
                "gender": "female",
                "email": "morgan.chen@example.test",
                "phone": "555-0102",
                "address": "24 Example Avenue",
            },
            {
                "name": "Riley Singh",
                "age": 27,
                "gender": "male",
                "email": "riley.singh@example.test",
                "phone": "555-0103",
                "address": "8 Demo Road",
            },
        ]
        doctors = [
            {
                "name": "Dr. Avery Brooks",
                "specialization": "Cardiology",
                "email": "avery.brooks@example.test",
                "phone": "555-0201",
            },
            {
                "name": "Dr. Casey Morgan",
                "specialization": "Family Medicine",
                "email": "casey.morgan@example.test",
                "phone": "555-0202",
            },
            {
                "name": "Dr. Quinn Patel",
                "specialization": "Neurology",
                "email": "quinn.patel@example.test",
                "phone": "555-0203",
            },
        ]

        patient_records = [
            Patient.objects.get_or_create(
                created_by=user,
                email=data["email"],
                defaults=data,
            )[0]
            for data in patients
        ]
        doctor_records = [
            Doctor.objects.get_or_create(
                email=data["email"],
                defaults={**data, "created_by": user},
            )[0]
            for data in doctors
        ]
        assignments = [
            (patient_records[0], doctor_records[0]),
            (patient_records[0], doctor_records[1]),
            (patient_records[1], doctor_records[2]),
            (patient_records[2], doctor_records[1]),
        ]
        for patient, doctor in assignments:
            PatientDoctorMapping.objects.get_or_create(
                patient=patient,
                doctor=doctor,
            )

        self.stdout.write(self.style.SUCCESS("Demo records are ready."))
        if created:
            self.stdout.write(f"Login email: {self.demo_email}")
            self.stdout.write(f"Login password: {self.demo_password}")
        else:
            self.stdout.write(
                f"Demo account already exists: {self.demo_email}"
            )
            self.stdout.write(
                "Its password was not changed; use the password already set for it."
            )
