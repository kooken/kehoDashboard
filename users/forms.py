import re
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, AuthenticationForm, \
    PasswordChangeForm
from django.core.exceptions import ValidationError
from users.models import User
from django import forms
from django.utils.translation import gettext_lazy as _


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'email' or field_name == 'username':
                field.widget.attrs['placeholder'] = 'Enter your email'
            elif field_name == 'password1' or field_name == 'password':
                field.widget.attrs['placeholder'] = 'Enter your password'
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Repeat your password'


class UserLoginForm(StyleFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Your email address'
        self.fields['password'].label = 'Your password'

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not email or not password:
            raise ValidationError("Both email and password are required.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("No account found with this email address.")

        if not user.check_password(password):
            raise ValidationError("Invalid email or password. Please try again.")

        if not user.is_active:
            raise ValidationError("This account is inactive. Please contact support.")

        self.cleaned_data['user'] = user
        return self.cleaned_data




class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'display_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'register-form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'register-form-control'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_password1'].label = _('Create new password')
        self.fields['new_password2'].label = _('Confirm new password')

        self.fields['new_password1'].error_messages = {
            'required': _('Please enter a password.'),
            'min_length': _('Your password must contain at least 8 characters.'),
            'too_common': _('This password is too common. Please choose a more secure one.'),
            'numeric': _('Password cannot be entirely numeric. Please include letters and symbols.')
        }
        self.fields.pop('old_password', None)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if len(password1) < 8:
            raise ValidationError(_('Your password must contain at least 8 characters.'))

        if not re.search(r'[A-Za-z]', password1) or not re.search(r'[0-9]', password1):
            raise ValidationError(_('Your password must include both letters and numbers.'))

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise ValidationError(_('Your password must include at least one special character (e.g., !@#$%^&*).'))

        if password1 != password2:
            raise ValidationError(_('Please make sure your passwords match.'))

        return password2

    class Meta:
        model = User
        fields = ('new_password1', 'new_password2')


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Email Address',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email address'
        }),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not User.objects.filter(email=email).exists():
            raise ValidationError('No account found with this email address.')

        return email


class DeleteAccountForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'register-form-control'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        if email != self.user.email:
            raise forms.ValidationError('The entered email does not match your account email.')
        return email


class CustomPasswordUpdateForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['old_password'].widget = forms.PasswordInput(attrs={
            'class': 'register-form-control',
        })
        self.fields['old_password'].label = _('Current Password')

        self.fields['new_password1'].widget = forms.PasswordInput(attrs={
            'class': 'register-form-control',
        })
        self.fields['new_password1'].label = _('New Password')
        self.fields['new_password1'].help_text = _(
            '<span class="custom-help-text">Must be at least 8 characters,'
            'and include numbers, letters, and special symbols.</span>'
        )

        self.fields['new_password2'].widget = forms.PasswordInput(attrs={
            'class': 'register-form-control',
        })
        self.fields['new_password2'].label = _('Confirm New Password')
        self.fields['new_password2'].help_text = ''

        self.fields['new_password1'].error_messages = {
            'required': _('Please enter a password.'),
            'min_length': _('Your password must contain at least 8 characters.'),
            'too_common': _('This password is too common. Please choose a more secure one.'),
            'numeric': _('Password cannot be entirely numeric. Please include letters and symbols.')
        }

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if len(password1) < 8:
            raise forms.ValidationError(_('Your password must contain at least 8 characters.'))

        if not re.search(r'[A-Za-z]', password1) or not re.search(r'[0-9]', password1):
            raise forms.ValidationError(_('Your password must include both letters and numbers.'))

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise forms.ValidationError(
                _('Your password must include at least one special character (e.g., !@#$%^&*).'))

        if password1 != password2:
            raise forms.ValidationError(_('Please make sure your passwords match.'))

        return password2
