"""
Forms for account onboarding flows.
"""
from typing import List

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


class PsychSignupStep1Form(forms.Form):
    """
    Step 1 form for Psychologist signup: account and personal details.
    """

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        # Use Django's password validators
        validate_password(password)
        return password


class PsychSignupStep2Form(forms.Form):
    """
    Step 2 form for Psychologist signup: professional & practice details.
    """

    registration_number = forms.CharField(max_length=50, required=False)
    registration_body = forms.CharField(max_length=100, required=False)
    years_experience = forms.IntegerField(min_value=0, required=False)

    # Professional profile
    bio = forms.CharField(widget=forms.Textarea, required=False)

    # Lists stored on model as JSON
    specialisms = forms.CharField(
        required=False,
        help_text="Comma-separated list (e.g., anxiety, depression)",
    )
    languages = forms.CharField(
        required=False,
        help_text="Comma-separated list (e.g., en, es, fr)",
    )

    # Service and modality
    service_nhs = forms.BooleanField(required=False)
    service_private = forms.BooleanField(required=False)
    modality = forms.ChoiceField(
        choices=(
            ("in_person", "In-Person"),
            ("remote", "Remote"),
            ("mixed", "Mixed"),
        ),
        initial="mixed",
    )

    # Location
    address_line_1 = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=50, required=False)
    postcode = forms.CharField(max_length=10, required=False)
    country = forms.CharField(max_length=50, required=False, initial="United Kingdom")

    # Capacity
    max_patients = forms.IntegerField(min_value=1, required=False)

    def cleaned_list(self, value: str) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def get_specialisms_list(self) -> List[str]:
        return self.cleaned_list(self.cleaned_data.get("specialisms"))

    def get_languages_list(self) -> List[str]:
        return self.cleaned_list(self.cleaned_data.get("languages"))
