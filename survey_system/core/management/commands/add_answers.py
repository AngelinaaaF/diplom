from django.core.management.base import BaseCommand
from core.models import StudentData, Survey, Form, Student, SurveyQuestion, Answer
import random

class Command(BaseCommand):
    help = 'Seeds answers for a selected survey'

    def add_arguments(self, parser):
        parser.add_argument('--survey-id', type=int, help='ID опроса')

    def handle(self, *args, **options):
        survey_id = options.get('survey_id')

        if not survey_id:
            surveys = Survey.objects.select_related('teacher_subject__group')
            self.stdout.write(self.style.NOTICE("📋 Доступные опросы:"))
            for s in surveys:
                group = s.teacher_subject.group if s.teacher_subject else None
                group_info = f"{group.program.name} ({group.admission_year})" if group else "—"
                self.stdout.write(f"  ID={s.id}: {s.name} — {s.year} | Группа: {group_info}")

            survey_id = input("\nВведите ID опроса: ").strip()

        try:
            survey = Survey.objects.select_related('teacher_subject__group').get(id=survey_id)
        except Survey.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Опрос с таким ID не найден"))
            return

        if not survey.teacher_subject or not survey.teacher_subject.group:
            self.stdout.write(self.style.ERROR("❌ У опроса нет связанного teacher_subject или группы"))
            return

        students = survey.teacher_subject.group.student_set.all()
        questions = SurveyQuestion.objects.filter(survey=survey).select_related('question')

        if not students.exists():
            self.stdout.write(self.style.ERROR("❌ В группе нет студентов"))
            return

        created_count = 0

        for student in students:
            form, created = Form.objects.get_or_create(
                student=student,
                survey=survey,
                defaults={'name': f"Ответ {student.full_name}"}
            )

            if not created:
                self.stdout.write(f"⚠️ Пропущено: у {student.full_name} уже есть форма")
                continue

            for sq in questions:
                Answer.objects.create(
                    form=form,
                    question=sq.question,
                    value=str(random.randint(1, 5))
                )
            try:
                StudentData.objects.create(
                    student=student,
                    avg_score=random.uniform(3.0, 5.0),
                    attendance_ratio=random.uniform(0.6, 1.0)
                )
            except Exception:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"\n✅ Добавлены ответы для {created_count} студентов"))
