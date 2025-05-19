from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, F, Value, CharField, IntegerField, FloatField, Sum
from django.db.models.functions import Concat, Cast
from django.db.models import ExpressionWrapper
from core.models import Answer, DepartmentStaff, UserProfile, Faculty, Survey

@login_required
def admin_rating_view(request):
    profile = request.user.userprofile
    teachers = DepartmentStaff.objects.select_related('department', 'department__faculty')

    if profile.role == UserProfile.Role.FACULTY_ADMIN:
        teachers = teachers.filter(department__faculty=profile.faculty)
    elif profile.role == UserProfile.Role.DEPARTMENT_ADMIN:
        teachers = teachers.filter(department=profile.department)

    faculty = request.GET.get('faculty')
    department = request.GET.get('department')
    subject = request.GET.get('subject')
    teacher_name = request.GET.get('teacher')
    group = request.GET.get('group')
    year = request.GET.get('year')
    mode = request.GET.get('mode', 'teacher')

    if faculty:
        teachers = teachers.filter(department__faculty__name__icontains=faculty)
    if department:
        teachers = teachers.filter(department__name__icontains=department)
    if teacher_name:
        teachers = teachers.filter(full_name__icontains=teacher_name)

    answers = Answer.objects.filter(
        form__survey__teacher_subject__teacher__in=teachers,
        question__type='choice'
    ).annotate(
        numeric=Cast('value', IntegerField()),
        weight=ExpressionWrapper(
            (Cast(F('form__student__data__avg_score'), FloatField()) / 5 + F('form__student__data__attendance_ratio')) / 2,
            output_field=FloatField()
        )
    )

    if subject:
        answers = answers.filter(form__survey__teacher_subject__subject__name__icontains=subject)
    if group:
        answers = answers.annotate(
            group_label=Concat(
                F('form__survey__teacher_subject__group__program__name'),
                Value(' '),
                F('form__survey__teacher_subject__group__admission_year'),
                output_field=CharField()
            )
        ).filter(group_label__icontains=group)
    if year:
        answers = answers.filter(form__survey__year=year)

    if mode == 'subject':
        rating = (
            answers.values(label=F('form__survey__teacher_subject__subject__name'))
            .annotate(
                avg_score=Avg('numeric'),
                weighted_score=Sum(F('numeric') * F('weight')) / Sum(F('weight'))
            ).order_by('-weighted_score')
        )
    else:
        rating = (
            answers.values(label=F('form__survey__teacher_subject__teacher__full_name'))
            .annotate(
                avg_score=Avg('numeric'),
                weighted_score=Sum(F('numeric') * F('weight')) / Sum(F('weight'))
            ).order_by('-weighted_score')
        )

    all_years = Survey.objects.filter(teacher_subject__teacher__in=teachers).values_list('year', flat=True).distinct()
    all_subjects = Survey.objects.filter(teacher_subject__teacher__in=teachers).values_list('teacher_subject__subject__name', flat=True).distinct()
    all_teachers = teachers.values_list('full_name', flat=True).distinct()
    all_groups = Survey.objects.filter(teacher_subject__teacher__in=teachers).annotate(
        group_label=Concat(
            F('teacher_subject__group__program__name'),
            Value(' '),
            F('teacher_subject__group__admission_year'),
            output_field=CharField()
        )
    ).values_list('group_label', flat=True).distinct()
    all_departments = teachers.values_list('department__name', flat=True).distinct()
    all_faculties = Faculty.objects.values_list('name', flat=True).distinct() if profile.role == UserProfile.Role.ADMIN else []

    return render(request, 'admin/rating.html', {
        'rating': rating,
        'all_years': all_years,
        'all_subjects': all_subjects,
        'all_teachers': all_teachers,
        'all_groups': all_groups,
        'all_departments': all_departments,
        'all_faculties': all_faculties,
    })
