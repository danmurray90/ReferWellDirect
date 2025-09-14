"""
Views for accounts app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User, Organisation, UserOrganisation
from .serializers import UserSerializer, OrganisationSerializer, UserOrganisationSerializer


class SignInView(TemplateView):
    """
    Sign-in page (stubbed for MVP).
    """
    template_name = 'accounts/signin.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('referrals:dashboard')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        # Stubbed authentication for MVP
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('referrals:dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
        
        return self.get(request, *args, **kwargs)


@login_required
def profile_view(request):
    """
    User profile page.
    """
    context = {
        'user': request.user,
        'organisations': UserOrganisation.objects.filter(user=request.user, is_active=True).select_related('organisation'),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def dashboard_view(request):
    """
    User dashboard based on user type.
    """
    user = request.user
    
    if user.is_gp:
        return redirect('referrals:gp_dashboard')
    elif user.is_patient:
        return redirect('referrals:patient_dashboard')
    elif user.is_psychologist:
        return redirect('catalogue:psychologist_dashboard')
    elif user.is_admin:
        return redirect('admin:index')
    else:
        return redirect('referrals:dashboard')


# API Views
class UserListAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter based on user permissions
        if self.request.user.is_admin:
            return User.objects.all()
        elif self.request.user.is_gp:
            # GPs can see patients they've referred
            return User.objects.filter(user_type=User.UserType.PATIENT)
        else:
            return User.objects.none()


class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


class OrganisationListAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating organisations.
    """
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter based on user permissions
        if self.request.user.is_admin:
            return Organisation.objects.all()
        else:
            # Users can see organisations they're associated with
            return Organisation.objects.filter(
                user_organisations__user=self.request.user,
                user_organisations__is_active=True
            )


class OrganisationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific organisation.
    """
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_user_to_organisation(request):
    """
    API endpoint to assign a user to an organisation.
    """
    user_id = request.data.get('user_id')
    organisation_id = request.data.get('organisation_id')
    role = request.data.get('role', UserOrganisation.Role.MEMBER)
    
    try:
        user = User.objects.get(id=user_id)
        organisation = Organisation.objects.get(id=organisation_id)
        
        # Check permissions
        if not request.user.is_admin and not request.user.is_high_touch_referrer:
            return Response(
                {'error': 'Insufficient permissions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create or update relationship
        user_org, created = UserOrganisation.objects.get_or_create(
            user=user,
            organisation=organisation,
            defaults={
                'role': role,
                'created_by': request.user
            }
        )
        
        if not created:
            user_org.role = role
            user_org.save()
        
        serializer = UserOrganisationSerializer(user_org)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Organisation.DoesNotExist:
        return Response({'error': 'Organisation not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
