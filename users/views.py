from django.contrib.auth.views import (LoginView, PasswordResetConfirmView,
                                       PasswordResetView)
from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.contrib.auth import update_session_auth_hash, logout, login
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from config.settings import EMAIL_HOST_USER
from django.urls import reverse_lazy
from users.forms import UserProfileForm, UserLoginForm, CustomPasswordResetForm, \
    CustomPasswordChangeForm, DeleteAccountForm, CustomPasswordUpdateForm
from users.models import User
from django.template.loader import render_to_string


def user_logout(request):
    logout(request)
    return redirect('main:index')


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('main:user_dashboard')

    def form_valid(self, form):
        user = form.cleaned_data.get('user')

        if user is not None and user.is_authenticated:
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            return super().form_valid(form)
        else:
            form.add_error(None, "Authentication failed. Please check your credentials.")
            return self.form_invalid(form)


class UserProfileView(LoginRequiredMixin, FormView):
    template_name = 'users/profile.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('users:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = 'users/change_password.html'
    form_class = CustomPasswordUpdateForm
    success_url = reverse_lazy('users:profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)


class DeleteAccountView(LoginRequiredMixin, FormView):
    template_name = 'users/delete_account.html'
    form_class = DeleteAccountForm
    success_url = reverse_lazy('main:index')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.request.user.delete()
        return super().form_valid(form)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    form_class = CustomPasswordChangeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['uidb64'] = self.kwargs.get('uidb64', '')
        context['token'] = self.kwargs.get('token', '')
        return context

    def form_valid(self, form):
        form.save()

        return redirect(reverse_lazy('users:login'))

    def form_invalid(self, form):
        return super().form_invalid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'emails/password_reset_email.html'
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = get_object_or_404(User, email=email)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode())

        host = self.request.get_host()
        reset_url = f'http://{host}{reverse_lazy("users:password_reset_confirm",
                                                 kwargs={"uidb64": uid, "token": token})}'

        html_message = render_to_string('emails/password_reset_email.html', {
            'email': user.email,
            'reset_url': reset_url,
        })

        text_message = f'Hello! Click on the link to reset your password: {reset_url}'

        email_message = EmailMultiAlternatives(
            subject="Password Reset Request",
            body=text_message,
            from_email=EMAIL_HOST_USER,
            to=[user.email],
        )
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()

        return render(self.request, self.template_name, {'form': form})

    def form_invalid(self, form):
        #     storage = messages.get_messages(self.request)
        #     storage.used = True
        return super().form_invalid(form)
