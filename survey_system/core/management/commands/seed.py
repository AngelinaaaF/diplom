from django.core.management.base import BaseCommand
from core.models import *
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Seeds the database with standardized CHOICE-only survey data'

    def handle(self, *args, **kwargs):
        # Faculties, Departments, Programs
        faculty = Faculty.objects.create(name="Engineering Faculty")
        department = Department.objects.create(name="Computer Science", faculty=faculty)
        program = Program.objects.create(name="Software Engineering", code="SE101", department=department)
        group = Group.objects.create(program=program, admission_year=2022)

        # Teacher
        user_teacher = User.objects.create(username="teacher1", password=make_password("pass123"))
        UserProfile.objects.create(user=user_teacher, role=UserProfile.Role.TEACHER)
        teacher = DepartmentStaff.objects.create(
            full_name="John Doe",
            position="Lecturer",
            degree="PhD",
            user=user_teacher,
            department=department
        )

        # Subject & TeacherSubject
        subject = Subject.objects.create(name="Databases", index="DB101")
        teacher_subject = TeacherSubject.objects.create(
            teacher=teacher,
            subject=subject,
            course=3,
            semester=2,
            group=group
        )

        # Student
        user_student = User.objects.create(username="student1", password=make_password("pass456"))
        UserProfile.objects.create(user=user_student, role=UserProfile.Role.STUDENT)
        student = Student.objects.create(
            full_name="Alice Smith",
            number="STU123",
            year=3,
            user=user_student,
            group=group
        )

        # Survey
        survey = Survey.objects.create(year=2024, name="Анкета оценки курса", teacher_subject=teacher_subject)
        scale_options = ["1", "2", "3", "4", "5"]

        def add_question(text, characteristic):
            question = QuestionBank.objects.create(text=text, characteristic=characteristic, type=QuestionBank.Type.CHOICE)
            for opt in scale_options:
                AnswerOption.objects.create(question=question, text=opt)
            SurveyQuestion.objects.create(survey=survey, question=question)

        # Block 1
        add_question("Оцените ваше общее впечатление от курса.", "Общее впечатление")
        add_question("Оцените качество полученных вами знаний в результате прохождения учебной дисциплины.", "Общее впечатление")

        # Block 2
        add_question("Оцените качество лекционного и практического материала.", "Содержание курса")
        add_question("Оцените качество подачи материала преподавателем.", "Содержание курса")
        add_question("Оцените общее содержание учебного материала в курсе.", "Содержание курса")

        # Block 3
        add_question("Насколько понятно преподаватель объясняет материал?", "Преподавание")
        add_question("Насколько преподаватель адаптирует сложные темы для понимания студентами?", "Преподавание")
        add_question("Насколько конструктивна обратная связь, предоставляемая преподавателем?", "Преподавание")
        add_question("Насколько справедливо и объективно преподаватель оценивает знания и усилия студентов?", "Преподавание")

        # Block 4
        add_question("Насколько удобны платформы для общения и проведения занятий?", "Организация и предмет")
        add_question("Насколько темп подачи материала соответствует вашим возможностям усвоения?", "Организация и предмет")
        add_question("Насколько учебные материалы (лекции, задания) соответствуют современным требованиям и актуальности дисциплины?", "Организация и предмет")
        add_question("Насколько дисциплина полезна для вашей будущей профессиональной деятельности?", "Организация и предмет")

        self.stdout.write(self.style.SUCCESS('✅ Standardized CHOICE-only survey data seeded successfully.'))
