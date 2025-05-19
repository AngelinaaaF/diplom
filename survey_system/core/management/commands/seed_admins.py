from django.core.management.base import BaseCommand
from core.models import Faculty, Department, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Seeds the database with admin-level users of different roles'

    def handle(self, *args, **kwargs):
        # Предполагаем, что факультет и кафедра уже существуют
        faculty = Faculty.objects.first()
        department = Department.objects.filter(faculty=faculty).first()

        if not faculty or not department:
            self.stdout.write(self.style.ERROR("❌ Не найдены Faculty и Department. Сначала запусти seed."))
            return

        def create_admin_user(username, role, faculty=None, department=None):
            user = User.objects.create(
                username=username,
                password=make_password("123")
            )
            UserProfile.objects.create(
                user=user,
                role=role,
                faculty=faculty if role == UserProfile.Role.FACULTY_ADMIN else None,
                department=department if role == UserProfile.Role.DEPARTMENT_ADMIN else None
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Создан {role}: {username}"))

        # create_admin_user("superadmin2", UserProfile.Role.ADMIN)
        #create_admin_user("facultyadmin", UserProfile.Role.FACULTY_ADMIN, faculty=faculty)
        create_admin_user("admin_2", UserProfile.Role.DEPARTMENT_ADMIN, department=department)
