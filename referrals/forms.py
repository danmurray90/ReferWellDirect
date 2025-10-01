"""
Forms for referrals app.
"""
from django import forms
from django.contrib.auth import get_user_model

from .models import Referral

User = get_user_model()


class ReferralForm(forms.ModelForm):
    """
    Form for creating and editing referrals.
    """

    class Meta:
        model = Referral
        fields = [
            "patient",
            "presenting_problem",
            "clinical_notes",
            "urgency_notes",
            "service_type",
            "modality",
            "priority",
            "preferred_latitude",
            "preferred_longitude",
            "max_distance_km",
            "preferred_language",
        ]
        widgets = {
            "presenting_problem": forms.Textarea(
                attrs={"rows": 4, "class": "form-control"}
            ),
            "clinical_notes": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"}
            ),
            "urgency_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "service_type": forms.Select(attrs={"class": "form-control"}),
            "modality": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "preferred_latitude": forms.NumberInput(
                attrs={"class": "form-control", "step": "any"}
            ),
            "preferred_longitude": forms.NumberInput(
                attrs={"class": "form-control", "step": "any"}
            ),
            "max_distance_km": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 500}
            ),
            "preferred_language": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter patients based on user type
        if user and user.is_gp:
            # GPs can refer any patient
            self.fields["patient"].queryset = User.objects.filter(
                user_type=User.UserType.PATIENT
            )
        elif user and user.is_patient:
            # Patients can only refer themselves
            self.fields["patient"].queryset = User.objects.filter(id=user.id)
            self.fields["patient"].initial = user
            self.fields["patient"].widget = forms.HiddenInput()
        else:
            self.fields["patient"].queryset = User.objects.none()

        # Set default values
        if not self.instance.pk:
            self.fields["max_distance_km"].initial = 50
            self.fields["preferred_language"].initial = "en"
            self.fields["service_type"].initial = Referral.ServiceType.NHS
            self.fields["modality"].initial = Referral.Modality.MIXED
            self.fields["priority"].initial = Referral.Priority.MEDIUM
