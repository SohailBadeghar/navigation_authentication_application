from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    RegistrationView,
    CustomPasswordChangeView,
    CustomPasswordChangeDoneView,
    DashboardView,
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,

    UserListView

)

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
    path('password-change-done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('users/', UserListView.as_view(), name='user_list'),

]
