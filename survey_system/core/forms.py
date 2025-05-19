from django import forms
from core.models import Survey, Faculty, Department, DepartmentStaff, Subject, Group, QuestionBank

class CombinedSurveyForm(forms.ModelForm):
    faculty = forms.ModelMultipleChoiceField(
        queryset=Faculty.objects.all(),
        required=False,
        label="Факультеты",
        widget=forms.SelectMultiple(attrs={'class': 'w-full border rounded px-2 py-1'})
    )
    department = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Кафедры",
        widget=forms.SelectMultiple(attrs={'class': 'w-full border rounded px-2 py-1'})
    )
    teacher = forms.ModelMultipleChoiceField(
        queryset=DepartmentStaff.objects.all(),
        required=False,
        label="Преподаватели",
        widget=forms.SelectMultiple(attrs={'class': 'w-full border rounded px-2 py-1'})
    )
    subject = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        label="Дисциплины",
        widget=forms.SelectMultiple(attrs={'class': 'w-full border rounded px-2 py-1'})
    )
    group = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Группы",
        widget=forms.SelectMultiple(attrs={'class': 'w-full border rounded px-2 py-1'})
    )

    questions = forms.ModelMultipleChoiceField(
        queryset=QuestionBank.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-1'}),
        label="Вопросы анкеты"
    )

    class Meta:
        model = Survey
        fields = ['name', 'year', 'start_date']
        labels = {
            'name': 'Название опроса',
            'year': 'Учебный год',
            'start_date': 'Дата начала',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'year': forms.NumberInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-2 py-1'}),
        }



class NewQuestionForm(forms.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['text', 'characteristic']
        labels = {
            'text': 'Текст вопроса',
            'characteristic': 'Характеристика',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Введите вопрос...',
                'class': 'border rounded w-full px-3 py-2 text-sm',
            }),
            'characteristic': forms.Select(attrs={
                'class': 'border rounded w-full px-3 py-2 text-sm',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = False
        self.fields['characteristic'].required = False
