
from core.admin_views import survey_wizard
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import load_questions_from_survey, student_home, start_survey, redirect_after_login,survey_results,teacher_home

from core.admin_views.admin.results import admin_results_view
from core.admin_views.admin.rating import admin_rating_view
from django.http import HttpResponse

from core.admin_views.survey_create import create_survey

from django.http import JsonResponse
from core.models import Faculty, Department, DepartmentStaff, Subject, Group, TeacherSubject

from django.http import JsonResponse
from core.models import TeacherSubject, Faculty, Department, DepartmentStaff, Subject, Group


def ajax_filter_fields_and_count(request):
    faculty_ids = request.GET.getlist('faculty[]')
    department_ids = request.GET.getlist('department[]')
    teacher_ids = request.GET.getlist('teacher[]')
    subject_ids = request.GET.getlist('subject[]')
    group_ids = request.GET.getlist('group[]')

    # 🔒 Строгая фильтрация только для расчета количества (итоговых TeacherSubject)
    ts_filtered = TeacherSubject.objects.all()
    if faculty_ids:
        ts_filtered = ts_filtered.filter(teacher__department__faculty__id__in=faculty_ids)
    if department_ids:
        ts_filtered = ts_filtered.filter(teacher__department__id__in=department_ids)
    if teacher_ids:
        ts_filtered = ts_filtered.filter(teacher__id__in=teacher_ids)
    if subject_ids:
        ts_filtered = ts_filtered.filter(subject__id__in=subject_ids)
    if group_ids:
        ts_filtered = ts_filtered.filter(group__id__in=group_ids)
    count = ts_filtered.distinct().count()

    # 🔄 Мягкая фильтрация — для опций в фильтрах
    ts_options = TeacherSubject.objects.all()
    if faculty_ids:
        ts_options = ts_options.filter(teacher__department__faculty__id__in=faculty_ids)
    if department_ids:
        ts_options = ts_options.filter(teacher__department__id__in=department_ids)
    if teacher_ids:
        ts_options = ts_options.filter(teacher__id__in=teacher_ids)
    if subject_ids:
        ts_options = ts_options.filter(subject__id__in=subject_ids)
    if group_ids:
        ts_options = ts_options.filter(group__id__in=group_ids)

    faculties = Faculty.objects.filter(
        id__in=ts_options.values_list('teacher__department__faculty__id', flat=True).distinct()
    )
    departments = Department.objects.filter(
        id__in=ts_options.values_list('teacher__department__id', flat=True).distinct()
    )
    teachers = DepartmentStaff.objects.filter(
        id__in=ts_options.values_list('teacher__id', flat=True).distinct()
    )
    subjects = Subject.objects.filter(
        id__in=ts_options.values_list('subject__id', flat=True).distinct()
    )
    groups = Group.objects.filter(
        id__in=ts_options.values_list('group__id', flat=True).distinct()
    )

    return JsonResponse({
        'faculties': [{'id': f.id, 'label': f.name} for f in faculties],
        'departments': [{'id': d.id, 'label': d.name} for d in departments],
        'teachers': [{'id': t.id, 'label': t.full_name} for t in teachers],
        'subjects': [{'id': s.id, 'label': s.name} for s in subjects],
        'groups': [{'id': g.id, 'label': str(g)} for g in groups],
        'count': count,
    })


urlpatterns = [
    path('teacher/admin/survey/create/', create_survey, name='create_survey'),
    path('teacher/admin/form/create/', survey_wizard.choose_or_create, name='choose_or_create'),
    path('teacher/admin/form/create/new/', survey_wizard.create_new_survey, name='create_new_survey'),
    path('teacher/admin/form/<int:survey_id>/edit/name/', survey_wizard.edit_survey_name, name='edit_survey_name'),
    path('teacher/admin/form/<int:survey_id>/edit/questions/', survey_wizard.edit_survey_questions, name='edit_survey_questions'),
    path('teacher/admin/form/<int:survey_id>/edit/settings/', survey_wizard.edit_survey_settings, name='edit_survey_settings'),
    path('admin/form/create/from/<int:source_id>/', survey_wizard.clone_survey, name='clone_survey'),


    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('home/', redirect_after_login, name='redirect_after_login'),
    path('student/home/', student_home, name='student_home'),
    path('survey/<int:survey_id>/start/', start_survey, name='start_survey'),
    path('teacher/home/', teacher_home, name='teacher_home'),
    path('survey/<int:survey_id>/results/', survey_results, name='survey_results'),
    path('teacher/admin/results/', admin_results_view, name='admin_results'),
    path('teacher/admin/rating/', admin_rating_view, name='admin_rating'),
    path('ajax/filter_fields_and_count/', ajax_filter_fields_and_count, name='filter_fields_and_count'),
        path('ajax/load_questions_from_survey/<int:survey_id>/', load_questions_from_survey, name='load_questions_from_survey'),

]
