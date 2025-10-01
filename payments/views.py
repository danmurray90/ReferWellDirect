"""
Views for payments app (stubbed).
"""
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView

from .models import Payment, PaymentMethod


class PaymentsView(LoginRequiredMixin, TemplateView):
    """
    Payments view (stubbed for MVP).
    """

    template_name = "payments/payments.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get recent payments
        context["recent_payments"] = Payment.objects.filter(user=user).order_by(
            "-created_at"
        )[:10]

        # Get payment methods
        context["payment_methods"] = PaymentMethod.objects.filter(
            user=user, is_active=True
        ).order_by("-is_default", "created_at")

        return context


class PaymentMethodListView(LoginRequiredMixin, ListView):
    """
    Payment method list view (stubbed for MVP).
    """

    model = PaymentMethod
    template_name = "payments/payment_method_list.html"
    context_object_name = "payment_methods"

    def get_queryset(self) -> Any:
        return PaymentMethod.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-is_default", "created_at")
