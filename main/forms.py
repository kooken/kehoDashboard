from django import forms


class LoginForm(forms.Form):
    password = forms.CharField(
        max_length=10,
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        label='Password'
    )
