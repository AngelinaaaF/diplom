from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from core.models import *
import random

class Command(BaseCommand):
    help = 'Полностью заполняет базу данных русскими данными и структурой опроса'

    def handle(self, *args, **kwargs):
        self.stdout.write("🧹 Удаляем старые данные...")
        for model in [
            Answer, Form, SurveyQuestion, Survey, AnswerOption, QuestionBank,
            TeacherSubject, Subject, DepartmentStaff, Student, Group, Program,
            Department, Faculty, UserProfile
        ]:
            model.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        self.stdout.write(self.style.SUCCESS("✅ База очищена"))

        scale = ["1", "2", "3", "4", "5"]

        def generate_unique_username(base):
            i = 1
            while User.objects.filter(username=f"{base}_{i}").exists():
                i += 1
            return f"{base}_{i}"

        def create_user(base_username, password, role, faculty=None, department=None):
            username = generate_unique_username(base_username)
            user = User.objects.create(username=username, password=make_password(password))
            UserProfile.objects.create(user=user, role=role, faculty=faculty, department=department)
            self.stdout.write(f"👤 Создан пользователь {username} [{role}]")
            return user

        def create_question(text, charac):
            q = QuestionBank.objects.create(text=text, characteristic=charac, type=QuestionBank.Type.CHOICE)
            for val in scale:
                AnswerOption.objects.create(question=q, text=val)
            return q

        faculty_data = {
            "Экономический факультет": ["Кафедра прикладной экономики", "Кафедра русского языка"],
            "Инженерный факультет": ["Кафедра прикладной инженерии", "Кафедра компьютерных технологий"]
        }

        first_names = ["Иван", "Пётр", "Сергей", "Алексей", "Дмитрий"]
        last_names = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов"]
        middle_name = "Николаевич"

        survey_template = None

        for f_index, (faculty_name, departments) in enumerate(faculty_data.items(), start=1):
            faculty = Faculty.objects.create(name=faculty_name)
            self.stdout.write(f"🏛 Создан факультет: {faculty.name}")

            for d_index, department_name in enumerate(departments, start=1):
                department = Department.objects.create(name=department_name, faculty=faculty)
                self.stdout.write(f"  🏢 Кафедра: {department.name}")

                for p_num in range(1, 3):
                    program_name = f"Направление {faculty.name.split()[0]}-{d_index}{p_num}"
                    program_code = f"{f_index}{d_index}{p_num}"
                    program = Program.objects.create(name=program_name, code=program_code, department=department)

                    for g_num in range(1, 3):
                        admission_year = 2020 + g_num
                        group = Group.objects.create(program=program, admission_year=admission_year)
                        self.stdout.write(f"    👥 Группа: {admission_year}")

                        for s in range(3):
                            fname = random.choice(first_names)
                            lname = random.choice(last_names)
                            base_username = f"{fname.lower()}_{lname.lower()}"
                            username = generate_unique_username(base_username)
                            full_name = f"{lname} {fname} {middle_name}"
                            user = User.objects.create(username=username, password=make_password("123"))
                            UserProfile.objects.create(user=user, role=UserProfile.Role.STUDENT)
                            Student.objects.create(full_name=full_name, number=f"S{username}", year=3, user=user, group=group)

                        for t in range(1, 3):
                            fname = random.choice(first_names)
                            lname = random.choice(last_names)
                            base_username = f"teacher_{lname.lower()}"
                            username = generate_unique_username(base_username)
                            full_name = f"{lname} {fname} {middle_name}"
                            user = User.objects.create(username=username, password=make_password("123"))
                            UserProfile.objects.create(user=user, role=UserProfile.Role.TEACHER)
                            teacher = DepartmentStaff.objects.create(
                                full_name=full_name,
                                position="Преподаватель",
                                degree="Кандидат наук",
                                user=user,
                                department=department
                            )

                            for subj_index in range(1, 3):
                                subj = Subject.objects.create(
                                    name=f"Дисциплина {lname} {subj_index}",
                                    index=f"SUBJ{f_index}{d_index}{t}{subj_index}"
                                )
                                ts = TeacherSubject.objects.create(
                                    teacher=teacher,
                                    subject=subj,
                                    course=3,
                                    semester=2,
                                    group=group
                                )
                                if not survey_template:
                                    survey_template = Survey.objects.create(
                                        name="Анкета оценки курса",
                                        year=2025,
                                        teacher_subject=ts
                                    )

        self.stdout.write("🧠 Добавляем вопросы в шаблон опроса...")

        def add_q(text, charac):
            q = create_question(text, charac)
            SurveyQuestion.objects.create(survey=survey_template, question=q)
            self.stdout.write(f"   ✅ {text}")

        add_q("Оцените ваше общее впечатление от курса.", "Общее впечатление")
        add_q("Оцените качество полученных вами знаний в результате прохождения учебной дисциплины.", "Общее впечатление")
        add_q("Оцените качество лекционного и практического материала.", "Содержание курса")
        add_q("Оцените качество подачи материала преподавателем.", "Содержание курса")
        add_q("Оцените общее содержание учебного материала в курсе.", "Содержание курса")
        add_q("Насколько понятно преподаватель объясняет материал?", "Преподавание")
        add_q("Насколько преподаватель адаптирует сложные темы для понимания студентами?", "Преподавание")
        add_q("Насколько конструктивна обратная связь, предоставляемая преподавателем?", "Преподавание")
        add_q("Насколько справедливо и объективно преподаватель оценивает знания и усилия студентов?", "Преподавание")
        add_q("Насколько удобны платформы для общения и проведения занятий?", "Организация и предмет")
        add_q("Насколько темп подачи материала соответствует вашим возможностям усвоения?", "Организация и предмет")
        add_q("Насколько учебные материалы соответствуют современным требованиям и актуальности дисциплины?", "Организация и предмет")
        add_q("Насколько дисциплина полезна для вашей будущей профессиональной деятельности?", "Организация и предмет")

        f1 = Faculty.objects.first()
        d1 = Department.objects.filter(faculty=f1).first()
        self.stdout.write("👮 Добавляем администраторов:")
        create_user("admin_office", "123", UserProfile.Role.ADMIN)
        create_user("faculty_admin", "123", UserProfile.Role.FACULTY_ADMIN, faculty=f1)
        create_user("dept_admin", "123", UserProfile.Role.DEPARTMENT_ADMIN, department=d1)

        self.stdout.write(self.style.SUCCESS("✅ Полное заполнение завершено."))