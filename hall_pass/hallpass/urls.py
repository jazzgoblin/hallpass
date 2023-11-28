# urls.py
from django.urls import path
from . import views
from .views import CustomLoginView, view_profile, passes_by_teacher, list_teachers, create_tenant_user

urlpatterns = [
    # Assuming your app is named 'hallpass'
    path('checkout/<int:student_id>/', views.checkout, name='checkout'),
    path('', views.students_out, name='list'),
    path('count/', views.student_passes_count, name='student_count'),
    path('view/<int:student_id>', views.view_passes, name='view' ),
    path('pass/<int:student_id>', views.individual_pass, name='pass' ),
    path('print/', views.all_student_passes, name='all_student_passes'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/profile/', view_profile, name='profile'),
    path('print/<int:teacher_id>', passes_by_teacher, name='teacher_passes'),
    path('teachers/', list_teachers, name='list_teachers'),
    path('administration/add_teacher', create_tenant_user, name='create_tenant_user'),
]
