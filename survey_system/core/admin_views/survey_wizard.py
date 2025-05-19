from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from core.models import Survey, TeacherSubject, QuestionBank, SurveyQuestion
from django import forms
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Q
from core.models import Survey, TeacherSubject, Department, Faculty, Group, Subject, DepartmentStaff


class SurveyNameForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['name', 'year']


class SurveySettingsForm(forms.ModelForm):
    faculty = forms.ModelMultipleChoiceField(
        queryset=Faculty.objects.all(),
        required=False,
        widget=forms.SelectMultiple
    )

    department = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.SelectMultiple
    )

    teacher = forms.ModelMultipleChoiceField(
        queryset=DepartmentStaff.objects.all(),
        required=False,
        widget=forms.SelectMultiple
    )

    subject = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.SelectMultiple
    )

    group = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple
    )

    class Meta:
        model = Survey
        fields = ['name', 'year', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SurveyStartDateForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['start_date']

class NewQuestionForm(forms.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['text', 'characteristic']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea', 'required': False}),
            'characteristic': forms.Select(attrs={'class': 'form-select', 'required': False}),
        }


@login_required
def choose_or_create(request):
    surveys = Survey.objects.all()
    return render(request, 'admin/form_wizard/choose_or_create.html', {'surveys': surveys})

@login_required
def create_new_survey(request):
    survey = Survey.objects.create(name='Новый опрос', year=timezone.now().year)
    return redirect('edit_survey_name', survey_id=survey.id)

@login_required
def edit_survey_name(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    form = SurveyNameForm(request.POST or None, instance=survey)
    if form.is_valid():
        form.save()
        return redirect('edit_survey_questions', survey_id=survey.id)
    return render(request, 'admin/form_wizard/edit_name.html', {'form': form, 'survey': survey})


@login_required
def edit_survey_questions(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    questions = QuestionBank.objects.all()
    selected_ids = set(survey.surveyquestion_set.values_list('question_id', flat=True))

    if request.method == 'POST' and 'add_question' in request.POST:
        new_question_form = NewQuestionForm(request.POST, prefix="new")
    else:
        new_question_form = NewQuestionForm(prefix="new")
    
    if request.method == 'POST':
        if 'add_question' in request.POST:
            if new_question_form.is_valid():
                new_q = new_question_form.save()
                SurveyQuestion.objects.create(survey=survey, question=new_q)
                return redirect('edit_survey_questions', survey_id=survey.id)

        elif 'next' in request.POST:
            survey.surveyquestion_set.all().delete()
            selected = request.POST.getlist('questions')
            for qid in selected:
                SurveyQuestion.objects.create(survey=survey, question_id=qid)
            return redirect('edit_survey_settings', survey_id=survey.id)

    return render(request, 'admin/form_wizard/edit_questions.html', {
        'survey': survey,
        'questions': questions,
        'selected_ids': selected_ids,
        'new_question_form': new_question_form,
    })

@login_required
def edit_survey_settings(request, survey_id):
    template_survey = get_object_or_404(Survey, id=survey_id)
    questions = template_survey.surveyquestion_set.all()

    if request.method == 'POST':
        form = SurveySettingsForm(request.POST)
        if form.is_valid():
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

            for ts in teacher_subjects:
                new_survey = Survey.objects.create(
                    name=form.cleaned_data['name'],
                    year=form.cleaned_data['year'],
                    start_date=form.cleaned_data['start_date'] or now().date(),
                    teacher_subject=ts
                )
                for sq in questions:
                    SurveyQuestion.objects.create(survey=new_survey, question=sq.question)

            return redirect('admin_results')  # или нужный тебе url name
    else:
        form = SurveySettingsForm(initial={
            'name': template_survey.name,
            'year': template_survey.year,
            'start_date': template_survey.start_date
        })

    return render(request, 'admin/form_wizard/edit_settings.html', {
        'form': form,
        'survey': template_survey
    })


@login_required
def clone_survey(request, source_id):
    source = get_object_or_404(Survey, id=source_id)

    new_survey = Survey.objects.create(
        name=source.name + " (копия)",
        year=source.year,
        teacher_subject=source.teacher_subject,
        start_date=source.start_date
    )

    for q in source.surveyquestion_set.all():
        SurveyQuestion.objects.create(survey=new_survey, question=q.question)

    return redirect('edit_survey_name', survey_id=new_survey.id)