from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import *
from django.contrib.auth import login
from django.db.models import Value, F, CharField
from django.db.models.functions import Concat

from core.results.survey_analysis import analyze_survey

@login_required
def survey_results(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)

    # Запускаем анализ
    result_dto = analyze_survey(survey)

    return render(request, 'survey/survey_results.html', {
        'survey': survey,
        'analysis': result_dto,
    })


@login_required
def teacher_home(request):
    teacher = get_object_or_404(DepartmentStaff, user=request.user)

    surveys = Survey.objects.filter(teacher_subject__teacher=teacher).select_related(
        'teacher_subject__subject',
        'teacher_subject__group__program'
    )

    # Получение параметров фильтра
    year = request.GET.get('year')
    name = request.GET.get('name')
    subject = request.GET.get('subject')
    group = request.GET.get('group')

    # Применение фильтров
    if year:
        surveys = surveys.filter(year=year)
    if name:
        surveys = surveys.filter(name__icontains=name)
    if subject:
        surveys = surveys.filter(teacher_subject__subject__name__icontains=subject)
    if group:
        surveys = surveys.annotate(
            group_label=Concat(
                F('teacher_subject__group__program__name'),
                Value(' '),
                F('teacher_subject__group__admission_year'),
                output_field=CharField()
            )
        ).filter(group_label__icontains=group)

    # Данные для выпадающих списков
    all_years = surveys.values_list('year', flat=True).distinct()
    all_names = surveys.values_list('name', flat=True).distinct()
    all_subjects = surveys.values_list('teacher_subject__subject__name', flat=True).distinct()
    all_groups = surveys.annotate(
        group_label=Concat(
            F('teacher_subject__group__program__name'),
            Value(' '),
            F('teacher_subject__group__admission_year'),
            output_field=CharField()
        )
    ).values_list('group_label', flat=True).distinct()

    return render(request, 'teacher/home.html', {
        'surveys': surveys.distinct(),
        'all_years': all_years,
        'all_names': all_names,
        'all_subjects': all_subjects,
        'all_groups': all_groups
    })


@login_required
def redirect_after_login(request):
    profile = UserProfile.objects.get(user=request.user)
    
    if profile.role == UserProfile.Role.STUDENT:
        return redirect('/student/home/')
    elif profile.role == UserProfile.Role.TEACHER:
        return redirect('/teacher/home/')
    elif profile.role == UserProfile.Role.ADMIN:
        return redirect('/teacher/admin/results/')
    elif profile.role == UserProfile.Role.DEPARTMENT_ADMIN:
        return redirect('/teacher/admin/results/')
    elif profile.role == UserProfile.Role.FACULTY_ADMIN:
        return redirect('/teacher/admin/results/')
    else:
        return redirect('/')


@login_required
def student_home(request):
    student = get_object_or_404(Student, user=request.user)

    surveys = Survey.objects.filter(teacher_subject__group=student.group)

    completed_ids = Form.objects.filter(student=student).values_list('survey_id', flat=True)

    if not request.GET.get('show_completed'):
        surveys = surveys.exclude(id__in=completed_ids)

    year = request.GET.get('year')
    name = request.GET.get('name')
    subject = request.GET.get('subject')
    teacher = request.GET.get('teacher')

    if year:
        surveys = surveys.filter(year=year)
    if name:
        surveys = surveys.filter(name__icontains=name)
    if subject:
        surveys = surveys.filter(teacher_subject__subject__name__icontains=subject)
    if teacher:
        surveys = surveys.filter(teacher_subject__teacher__full_name__icontains=teacher)

    all_years = surveys.values_list('year', flat=True).distinct()
    all_subjects = surveys.values_list('teacher_subject__subject__name', flat=True).distinct()
    all_teachers = surveys.values_list('teacher_subject__teacher__full_name', flat=True).distinct()
    all_names = surveys.values_list('name', flat=True).distinct()
    

    return render(request, 'student/home.html', {
        'surveys': surveys.distinct(),
        'all_years': all_years,
        'all_subjects': all_subjects,
        'all_teachers': all_teachers,
        'all_names': all_names,
        'completed_ids': completed_ids, 
    })


@login_required
def start_survey(request, survey_id):
    student = get_object_or_404(Student, user=request.user)
    survey = get_object_or_404(Survey, id=survey_id)

    # Проверим, не прошёл ли уже
    if Form.objects.filter(survey=survey, student=student).exists():
        return render(request, 'student/already_done.html')

    questions = SurveyQuestion.objects.filter(survey=survey).select_related('question')

    if request.method == 'POST':
        form = Form.objects.create(
            name=f"{student.full_name} – {survey.name}",
            survey=survey,
            student=student
        )

        for item in questions:
            q = item.question

            # обрабатываем по типу
            if q.type == QuestionBank.Type.TEXT:
                value = request.POST.get(f'question_{item.id}', '').strip()

            elif q.type == QuestionBank.Type.CHOICE:
                value = request.POST.get(f'question_{item.id}', '').strip()

            elif q.type == QuestionBank.Type.MULTI:
                selected = request.POST.getlist(f'question_{item.id}_multi')
                value = ', '.join(selected)

            else:
                value = ''

            if value:
                Answer.objects.create(
                    form=form,
                    question=q,
                    value=value
                )

        return redirect('student_home')

    return render(request, 'student/start_survey.html', {
        'survey': survey,
        'questions': questions
    })


@login_required
def load_questions_from_survey(request, survey_id):
    questions = SurveyQuestion.objects.filter(survey_id=survey_id).select_related('question')

    result = [
        {"id": q.question.id, "text": q.question.text}
        for q in questions
    ]
    return JsonResponse({"questions": result})