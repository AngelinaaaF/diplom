from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from core.models import Survey, TeacherSubject, SurveyQuestion, QuestionBank
from core.forms import CombinedSurveyForm, NewQuestionForm
from django.contrib import messages

@login_required
def create_survey(request):
    form = CombinedSurveyForm(request.POST or None)
    new_question_form = NewQuestionForm(request.POST or None, prefix="new")
    all_questions = QuestionBank.objects.all()
    existing_surveys = Survey.objects.filter(
        id__in=SurveyQuestion.objects.values_list('survey_id', flat=True).distinct()
    )
    if request.method == 'POST':
        if 'add_question' in request.POST and new_question_form.is_valid():
            new_q = new_question_form.save()
            # повторный рендер с уже добавленным вопросом
            form = CombinedSurveyForm()  # очищаем фильтры
        elif 'submit_all' in request.POST and form.is_valid():
            filters = Q()
            faculties = form.cleaned_data.get('faculty')
            departments = form.cleaned_data.get('department')
            teachers = form.cleaned_data.get('teacher')
            subjects = form.cleaned_data.get('subject')
            groups = form.cleaned_data.get('group')

            if departments:                         
                filters &= Q(teacher__department__in=departments)
            elif faculties:
                filters &= Q(teacher__department__faculty__in=faculties)
            if teachers:
                filters &= Q(teacher__in=teachers)
            if subjects:
                filters &= Q(subject__in=subjects)
            if groups:
                filters &= Q(group__in=groups)

            teacher_subjects = TeacherSubject.objects.filter(filters).distinct()
            questions = form.cleaned_data.get('questions')

            duplicates = []
            for ts in teacher_subjects:
                exists = Survey.objects.filter(
                    teacher_subject=ts,
                    year=form.cleaned_data['year']
                ).exists()
                if exists:
                    duplicates.append(f"{ts.teacher.full_name} — {ts.subject.name} — {ts.group.number}")

            if duplicates:
                print("ggleglel")
                messages.error(request, "Опрос уже существует для:\n" + "\n".join(duplicates))

                return render(request, 'admin/survey_create.html', {
                    'form': form,
                    'new_question_form': new_question_form,
                    'all_questions': all_questions,
                    'existing_surveys': existing_surveys,
                })
            else:
                for ts in teacher_subjects:
                    survey = Survey.objects.create(
                        name=form.cleaned_data['name'],
                        year=form.cleaned_data['year'],
                        start_date=form.cleaned_data['start_date'] or now().date(),
                        teacher_subject=ts
                    )
                    for q in questions:
                        SurveyQuestion.objects.create(survey=survey, question=q)
                return redirect('admin_results')



    return render(request, 'admin/survey_create.html', {
        'form': form,
        'new_question_form': new_question_form,
        'all_questions': all_questions,
        'existing_surveys': existing_surveys,
    })
