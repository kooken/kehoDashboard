from django.urls import path
from users.apps import UsersConfig
from users.views import UserLoginView,UserProfileView, CustomPasswordResetView, \
    CustomPasswordResetConfirmView, ChangePasswordView, \
    DeleteAccountView, user_logout

app_name = UsersConfig.name

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
