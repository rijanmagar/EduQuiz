# quiz/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()
class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    user_type = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher')],
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        required=True
    )
    lcid = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter LCID'})
    )
    teacher_id = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Teacher ID'})
    )

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        lcid = cleaned_data.get('lcid')
        teacher_id = cleaned_data.get('teacher_id')
        if user_type == 'student' and not lcid:
            self.add_error('lcid', 'LCID is required for students.')
        if user_type == 'teacher' and not teacher_id:
            self.add_error('teacher_id', 'Teacher ID is required for teachers.')
        return cleaned_data

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
    )
    user_type = forms.ChoiceField(
        choices=[('student', 'Student'), ('teacher', 'Teacher')],
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        required=True
    )
    lcid = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter LCID'})
    )
    teacher_id = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Teacher ID'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type', 'lcid', 'teacher_id']

    def clean(self):

        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        lcid = cleaned_data.get('lcid')
        teacher_id = cleaned_data.get('teacher_id')
        if user_type == 'student' and not lcid:
            self.add_error('lcid', 'LCID is required for students.')
        if user_type == 'teacher' and not teacher_id:
            self.add_error('teacher_id', 'Teacher ID is required for teachers.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user_type = self.cleaned_data.get('user_type')
        user.is_student = user_type == 'student'
        user.is_teacher = user_type == 'teacher'
        user.lcid = self.cleaned_data.get('lcid') if user.is_student else None
        user.teacher_id = self.cleaned_data.get('teacher_id') if user.is_teacher else None
        if commit:
            user.save()
        return user