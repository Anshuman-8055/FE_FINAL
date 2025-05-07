from django.urls import path, include
from jobapp import views

app_name = "jobapp"


urlpatterns = [
    path('api/jobs/', views.job_list_api_view, name='job-list-api'),
    path('', views.home_view, name='home'),
    path('jobs/', views.job_list_View, name='job-list'),
    path('job/create/', views.create_job_View, name='create-job'),
    path('job/<int:id>/', views.single_job_view, name='single-job'),
    path('apply-job/<int:id>/', views.apply_job_view, name='apply-job'),
    path('bookmark-job/<int:id>/', views.job_bookmark_view, name='bookmark-job'),
    path('about/', views.about_us_view, name='about'),
    path('contact-us/', views.contact_us_view, name='contact-us'),
    path('result/', views.search_result_view, name='search_result'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/employer/job/<int:id>/applicants/', views.all_applicants_view, name='applicants'),
    path('dashboard/employer/job/edit/<int:id>', views.job_edit_view, name='edit-job'),
    path('dashboard/employer/applicant/<int:id>/', views.applicant_details_view, name='applicant-details'),
    path('dashboard/employer/close/<int:id>/', views.make_complete_job_view, name='complete'),
    path('dashboard/employer/delete/<int:id>/', views.delete_job_view, name='delete'),
    path('dashboard/employee/delete-bookmark/<int:id>/', views.delete_bookmark_view, name='delete-bookmark'),
    path('dashboard/employee/remove-application/<int:id>/', views.remove_application_view, name='remove-application'),
    path('remove-application/<int:id>/', views.remove_application_view, name='remove-application'),
    path('about-us/', views.about_us_view, name='about-us'),
    path('admin-dashboard/', views.superuser_dashboard_view, name='admin-dashboard'),
    path('view-resume/<int:application_id>/', views.view_resume, name='view-resume'),
    path('rate-job/<int:id>/', views.rate_job_view, name='rate-job'),
    path('delete-test-message/', views.delete_test_message, name='delete-test-message'),
    path('update-application-status/<int:application_id>/<str:status>/', views.update_application_status, name='update-application-status'),
    path('view-flask-application/<int:application_id>/', views.view_flask_application, name='view-flask-application'),
    path('view-application/<int:application_id>/', views.view_application, name='view-application'),
]
