from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Value, F, CharField
from django.db.models.functions import Concat
from collections import defaultdict
from statistics import mean
from core.models import Survey, Answer, StudentData, Student, UserProfile


def get_weight(student: Student) -> float:
    try:
        data = student.data
        grades = data.avg_score
        attendance = data.attendance_ratio
    except StudentData.DoesNotExist:
        grades = 4.0
        attendance = 0.9
    return (grades / 5 + attendance) / 2


@login_required
def admin_results_view(request):
    profile = request.user.userprofile
    surveys = Survey.objects.exclude(teacher_subject__isnull=True).select_related(
        'teacher_subject__subject',
        'teacher_subject__teacher__department__faculty',
        'teacher_subject__group__program'
    )

    if profile.role == UserProfile.Role.FACULTY_ADMIN:
        surveys = surveys.filter(teacher_subject__teacher__department__faculty=profile.faculty)
    elif profile.role == UserProfile.Role.DEPARTMENT_ADMIN:
        surveys = surveys.filter(teacher_subject__teacher__department=profile.department)

    filters = {
        "faculty": request.GET.get("faculty"),
        "department": request.GET.get("department"),
        "subject": request.GET.get("subject"),
        "teacher": request.GET.get("teacher"),
        "group": request.GET.get("group"),
        "year": request.GET.get("year"),
        "name": request.GET.get("name"),
    }

    if filters["faculty"]:
        surveys = surveys.filter(teacher_subject__teacher__department__faculty__name=filters["faculty"])
    if filters["department"]:
        surveys = surveys.filter(teacher_subject__teacher__department__name=filters["department"])
    if filters["subject"]:
        surveys = surveys.filter(teacher_subject__subject__name=filters["subject"])
    if filters["teacher"]:
        surveys = surveys.filter(teacher_subject__teacher__full_name=filters["teacher"])
    if filters["group"]:
        surveys = surveys.annotate(
            group_label=Concat(
                F('teacher_subject__group__program__name'),
                Value(' '),
                F('teacher_subject__group__admission_year'),
                output_field=CharField()
            )
        ).filter(group_label=filters["group"])
    if filters["year"]:
        surveys = surveys.filter(year=filters["year"])
    if filters["name"]:
        surveys = surveys.filter(name__icontains=filters["name"])

    all_faculties = surveys.values_list('teacher_subject__teacher__department__faculty__name', flat=True).distinct()
    all_departments = surveys.values_list('teacher_subject__teacher__department__name', flat=True).distinct()
    all_subjects = surveys.values_list('teacher_subject__subject__name', flat=True).distinct()
    all_teachers = surveys.values_list('teacher_subject__teacher__full_name', flat=True).distinct()
    all_names = surveys.values_list('name', flat=True).distinct()
    all_years = surveys.values_list('year', flat=True).distinct()
    all_groups = surveys.annotate(
        group_label=Concat(
            F('teacher_subject__group__program__name'),
            Value(' '),
            F('teacher_subject__group__admission_year'),
            output_field=CharField()
        )
    ).values_list('group_label', flat=True).distinct()

    # Пост-обработка: расчёт средних оценок вручную
    survey_map = {s.id: s for s in surveys}
    survey_ids = list(survey_map.keys())
    answers = Answer.objects.filter(form__survey_id__in=survey_ids, question__type='choice').select_related('form__student')

    grouped = defaultdict(list)
    weighted = defaultdict(lambda: {"total": 0.0, "weight_sum": 0.0})

    for a in answers:
        try:
            value = int(a.value)
        except ValueError:
            continue
        sid = a.form.survey_id
        grouped[sid].append(value)

        weight = get_weight(a.form.student)
        weighted[sid]["total"] += value * weight
        weighted[sid]["weight_sum"] += weight

    for sid, survey in survey_map.items():
        scores = grouped[sid]
        survey.avg_score = round(mean(scores), 2) if scores else None

        if weighted[sid]["weight_sum"]:
            survey.weighted_score = round(weighted[sid]["total"] / weighted[sid]["weight_sum"], 2)
        else:
            survey.weighted_score = None

    return render(request, 'admin/results.html', {
        'surveys': survey_map.values(),
        'all_faculties': all_faculties,
        'all_departments': all_departments,
        'all_subjects': all_subjects,
        'all_teachers': all_teachers,
        'all_names': all_names,
        'all_years': all_years,
        'all_groups': all_groups,
    })
