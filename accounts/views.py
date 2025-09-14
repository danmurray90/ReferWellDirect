"""
Views for the accounts app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from .models import User, Organisation
from .serializers import UserSerializer, OrganisationSerializer


def home(request):
    """
    Home page view.
    """
    context = {
        'title': 'ReferWell Direct',
        'description': 'Intelligent referral matching for mental health services',
    }
    return render(request, 'accounts/home.html', context)


@login_required
def dashboard(request):
    """
    User dashboard view.
    """
    user = request.user
    context = {
        'title': f'Dashboard - {user.get_full_name()}',
        'user': user,
        'user_type': user.get_user_type_display(),
    }
    return render(request, 'accounts/dashboard.html', context)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user information.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class OrganisationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Organisation model.
    """
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search organisations by name or postcode.
        """
        query = request.GET.get('q', '')
        if query:
            organisations = self.queryset.filter(
                models.Q(name__icontains=query) |
                models.Q(postcode__icontains=query)
            )
        else:
            organisations = self.queryset.none()
        
        serializer = self.get_serializer(organisations, many=True)
        return Response(serializer.data)