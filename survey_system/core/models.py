from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Faculty(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=255)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'
        ADMIN = 'admin', 'Admin (Global)'
        FACULTY_ADMIN = 'faculty_admin', 'Admin (Faculty)'
        DEPARTMENT_ADMIN = 'department_admin', 'Admin (Department)'
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices)
    faculty = models.ForeignKey(Faculty, null=True, blank=True, on_delete=models.SET_NULL)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    def get_full_name(self):
            if self.role == self.Role.STUDENT and hasattr(self.user, "student"):
                return self.user.student.full_name
            elif self.role == self.Role.TEACHER and hasattr(self.user, "departmentstaff"):
                return self.user.departmentstaff.full_name
            return self.user.username  # fallback

    def __str__(self):
            return f"{self.get_full_name()} ({self.role})"
    
class Program(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.name}"

class Group(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    admission_year = models.IntegerField()
    number = models.CharField(max_length=10)
    def __str__(self):
        year_suffix = str(self.admission_year)[-2:]  # последние две цифры
        return f"№{year_suffix}{self.program.code}{self.number}"


class DepartmentStaff(models.Model):
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    def __str__(self):
        return self.full_name

class Subject(models.Model):
    name = models.CharField(max_length=255)
    index = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(DepartmentStaff, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    course = models.IntegerField()
    semester = models.IntegerField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

class Student(models.Model):
    full_name = models.CharField(max_length=255)
    number = models.CharField(max_length=50)
    year = models.IntegerField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.full_name}"

class Survey(models.Model):
    year = models.IntegerField()
    name = models.CharField(max_length=255)
    teacher_subject = models.ForeignKey(TeacherSubject, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True, default=timezone.now)
    def __str__(self):
        return f"{self.name}"

class QuestionBank(models.Model):
    class Type(models.TextChoices):
        TEXT = 'text', 'Открытый'
        CHOICE = 'choice', 'Выбор одного варианта'
        MULTI = 'multi', 'Выбор нескольких вариантов'
    class Characteristic(models.TextChoices):
        GENERAL = 'Общее впечатление', 'Общее впечатление'
        CONTENT = 'Содержание курса', 'Содержание курса'
        TEACHING = 'Преподавание', 'Преподавание'
        ORGANIZATION = 'Организация и предмет', 'Организация и предмет'
    text = models.TextField()
    characteristic = models.CharField(max_length=100, choices=Characteristic.choices)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.CHOICE)
    def __str__(self):
        return f"{self.text}    "

class AnswerOption(models.Model):
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text

class SurveyQuestion(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE)

class Form(models.Model):
    name = models.CharField(max_length=255)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

class Answer(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    question = models.ForeignKey(QuestionBank, on_delete=models.CASCADE)
    value = models.TextField()

class StudentData(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='data')
    avg_score = models.FloatField(default=4.0, verbose_name="Средний балл")
    attendance_ratio = models.FloatField(default=0.9, verbose_name="Посещаемость (0-1)")

    def __str__(self):
        return f"{self.student.full_name} — балл: {self.avg_score}, посещаемость: {self.attendance_ratio}"