from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Group, Student
import random

FIRST_NAMES = ['Иван', 'Алексей', 'Мария', 'Ольга', 'Светлана', 'Дмитрий', 'Андрей', 'Татьяна']
LAST_NAMES = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Новиков', 'Морозов']
MIDDLE_NAMES = ['Александрович', 'Ивановна', 'Петрович', 'Сергеевна', 'Владимирович']

class Command(BaseCommand):
    help = 'Создаёт случайных студентов в выбранной группе'

    def add_arguments(self, parser):
        parser.add_argument('--group-id', type=int, required=True, help='ID группы')
        parser.add_argument('--count', type=int, default=10, help='Количество студентов (по умолчанию 10)')

    def handle(self, *args, **options):
        group_id = options['group_id']
        count = options['count']

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Группа с таким ID не найдена'))
            return

        created = 0
        for i in range(count):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            mn = random.choice(MIDDLE_NAMES)
            full_name = f"{ln} {fn} {mn}"
            number = f"{random.randint(10000, 99999)}"

            user = User.objects.create_user(
                username=f"student_{ln.lower()}_{random.randint(100,999)}",
                password="12345678"
            )

            Student.objects.create(
                user=user,
                full_name=full_name,
                number=number,
                year=group.admission_year,
                group=group
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Добавлено студентов: {created}"))
