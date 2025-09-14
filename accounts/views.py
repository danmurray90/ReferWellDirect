"""
Views for the accounts app.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models, transaction
from .models import User, Organisation, UserOrganisation, OnboardingStep, UserOnboardingProgress, OnboardingSession
from .serializers import (
    UserSerializer, OrganisationSerializer, OnboardingStepSerializer,
    UserOnboardingProgressSerializer, OnboardingSessionSerializer,
    OnboardingProgressUpdateSerializer, OnboardingStepDataSerializer
)


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


@csrf_protect
@require_http_methods(["GET", "POST"])
def signin(request):
    """
    User sign in view.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'referrals:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please provide both email and password.')
    
    return render(request, 'accounts/signin.html')


@require_http_methods(["POST"])
def signout(request):
    """
    User sign out view.
    """
    logout(request)
    messages.success(request, 'You have been signed out successfully.')
    return redirect('accounts:home')


@csrf_protect
@require_http_methods(["GET", "POST"])
def signup(request):
    """
    User sign up view.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type')
        
        if all([email, password, first_name, last_name, user_type]):
            try:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=user_type
                )
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('accounts:dashboard')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'accounts/signup.html')


@login_required
def profile(request):
    """
    User profile view.
    """
    user = request.user
    context = {
        'title': f'Profile - {user.get_full_name()}',
        'user': user,
    }
    return render(request, 'accounts/profile.html', context)


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


# Onboarding Views

@login_required
def onboarding_start(request):
    """
    Start the onboarding process for a user.
    """
    user = request.user
    
    # Check if user already has an onboarding session
    session, created = OnboardingSession.objects.get_or_create(
        user=user,
        defaults={'status': OnboardingSession.Status.NOT_STARTED}
    )
    
    if session.status == OnboardingSession.Status.COMPLETED:
        messages.info(request, "You have already completed the onboarding process.")
        return redirect('accounts:dashboard')
    
    # Start the session if not already started
    if session.status == OnboardingSession.Status.NOT_STARTED:
        session.start()
    
    # Create progress records for all steps if they don't exist
    steps = OnboardingStep.objects.filter(
        user_type=user.user_type,
        is_active=True
    ).order_by('order')
    
    for step in steps:
        UserOnboardingProgress.objects.get_or_create(
            user=user,
            step=step,
            defaults={'status': UserOnboardingProgress.Status.PENDING}
        )
    
    return redirect('accounts:onboarding_step', step_id=session.current_step.id)


@login_required
def onboarding_step(request, step_id):
    """
    Display a specific onboarding step.
    """
    user = request.user
    step = get_object_or_404(OnboardingStep, id=step_id, is_active=True)
    
    # Check if user has access to this step
    if step.user_type != user.user_type:
        messages.error(request, "You don't have access to this step.")
        return redirect('accounts:dashboard')
    
    # Get or create progress record
    progress, created = UserOnboardingProgress.objects.get_or_create(
        user=user,
        step=step,
        defaults={'status': UserOnboardingProgress.Status.PENDING}
    )
    
    # Mark as started if not already
    if progress.status == UserOnboardingProgress.Status.PENDING:
        progress.mark_started()
    
    # Get all steps for this user type for progress indicator
    all_steps = OnboardingStep.objects.filter(
        user_type=user.user_type,
        is_active=True
    ).order_by('order')
    
    # Get next step
    session = user.onboarding_session
    next_step = session.get_next_step()
    
    # Calculate progress percentage
    total_steps = all_steps.count()
    completed_steps = user.onboarding_progress.filter(
        status=UserOnboardingProgress.Status.COMPLETED
    ).count()
    progress_percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 100
    
    context = {
        'title': f'Onboarding - {step.name}',
        'step': step,
        'progress': progress,
        'user': user,
        'all_steps': all_steps,
        'next_step': next_step,
        'progress_percentage': progress_percentage,
    }
    
    # Add step-specific context
    if step.step_type == OnboardingStep.StepType.PROFILE_SETUP:
        context['form_data'] = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'date_of_birth': user.date_of_birth,
        }
    elif step.step_type == OnboardingStep.StepType.ORGANISATION_SETUP:
        # Get user's organisations
        user_orgs = user.user_organisations.filter(is_active=True)
        context['user_organisations'] = user_orgs
    elif step.step_type == OnboardingStep.StepType.PREFERENCES:
        context['form_data'] = {
            'preferred_language': user.preferred_language,
            'timezone': user.timezone,
        }
    
    return render(request, f'accounts/onboarding/{step.step_type}.html', context)


@login_required
def onboarding_complete_step(request, step_id):
    """
    Complete a specific onboarding step.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    step = get_object_or_404(OnboardingStep, id=step_id, is_active=True)
    
    # Check if user has access to this step
    if step.user_type != user.user_type:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get progress record
    try:
        progress = UserOnboardingProgress.objects.get(user=user, step=step)
    except UserOnboardingProgress.DoesNotExist:
        return JsonResponse({'error': 'Progress record not found'}, status=404)
    
    # Validate and process step data
    step_data = {}
    
    if step.step_type == OnboardingStep.StepType.PROFILE_SETUP:
        # Update user profile
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        if request.POST.get('date_of_birth'):
            user.date_of_birth = request.POST.get('date_of_birth')
        user.save()
        
        step_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'date_of_birth': str(user.date_of_birth) if user.date_of_birth else None,
        }
    
    elif step.step_type == OnboardingStep.StepType.ORGANISATION_SETUP:
        # Handle organisation setup
        org_name = request.POST.get('organisation_name')
        org_type = request.POST.get('organisation_type')
        
        if org_name and org_type:
            # Create or find organisation
            organisation, created = Organisation.objects.get_or_create(
                name=org_name,
                defaults={
                    'organisation_type': org_type,
                    'created_by': user,
                }
            )
            
            # Create user-organisation relationship
            UserOrganisation.objects.get_or_create(
                user=user,
                organisation=organisation,
                defaults={
                    'role': UserOrganisation.Role.OWNER if created else UserOrganisation.Role.MEMBER,
                    'created_by': user,
                }
            )
            
            step_data = {
                'organisation_name': org_name,
                'organisation_type': org_type,
                'organisation_id': str(organisation.id),
            }
    
    elif step.step_type == OnboardingStep.StepType.PREFERENCES:
        # Update user preferences
        user.preferred_language = request.POST.get('preferred_language', user.preferred_language)
        user.timezone = request.POST.get('timezone', user.timezone)
        user.save()
        
        step_data = {
            'preferred_language': user.preferred_language,
            'timezone': user.timezone,
        }
    
    # Mark step as completed
    progress.mark_completed(step_data)
    
    # Check if onboarding is complete
    session = user.onboarding_session
    next_step = session.get_next_step()
    
    if next_step:
        # Redirect to next step
        return redirect('accounts:onboarding_step', step_id=next_step.id)
    else:
        # Complete onboarding
        session.complete()
        messages.success(request, "Congratulations! You have completed the onboarding process.")
        return redirect('accounts:dashboard')


@login_required
def onboarding_skip_step(request, step_id):
    """
    Skip a specific onboarding step.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    step = get_object_or_404(OnboardingStep, id=step_id, is_active=True)
    
    # Check if user has access to this step
    if step.user_type != user.user_type:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get progress record
    try:
        progress = UserOnboardingProgress.objects.get(user=user, step=step)
    except UserOnboardingProgress.DoesNotExist:
        return JsonResponse({'error': 'Progress record not found'}, status=404)
    
    # Skip step if it's not required
    if step.is_required:
        return JsonResponse({'error': 'This step is required and cannot be skipped'}, status=400)
    
    # Mark step as skipped
    progress.mark_skipped()
    
    # Check if onboarding is complete
    session = user.onboarding_session
    next_step = session.get_next_step()
    
    if next_step:
        # Redirect to next step
        return redirect('accounts:onboarding_step', step_id=next_step.id)
    else:
        # Complete onboarding
        session.complete()
        messages.success(request, "You have completed the onboarding process.")
        return redirect('accounts:dashboard')


@login_required
def onboarding_progress(request):
    """
    Get onboarding progress for the current user.
    """
    user = request.user
    
    try:
        session = user.onboarding_session
    except OnboardingSession.DoesNotExist:
        return JsonResponse({'error': 'No onboarding session found'}, status=404)
    
    # Get all progress records
    progress_records = UserOnboardingProgress.objects.filter(user=user).select_related('step')
    
    # Calculate progress
    total_steps = OnboardingStep.objects.filter(
        user_type=user.user_type,
        is_active=True
    ).count()
    
    completed_steps = progress_records.filter(
        status=UserOnboardingProgress.Status.COMPLETED
    ).count()
    
    progress_percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 100
    
    # Get current step
    current_step = session.current_step
    
    # Get all steps with their status
    steps = []
    for step in OnboardingStep.objects.filter(
        user_type=user.user_type,
        is_active=True
    ).order_by('order'):
        try:
            progress = progress_records.get(step=step)
            step_status = progress.status
        except UserOnboardingProgress.DoesNotExist:
            step_status = UserOnboardingProgress.Status.PENDING
        
        steps.append({
            'id': str(step.id),
            'name': step.name,
            'step_type': step.step_type,
            'order': step.order,
            'is_required': step.is_required,
            'status': step_status,
            'is_current': current_step and step.id == current_step.id,
        })
    
    return JsonResponse({
        'session': {
            'id': str(session.id),
            'status': session.status,
            'progress_percentage': progress_percentage,
            'current_step_id': str(current_step.id) if current_step else None,
        },
        'steps': steps,
    })


# API Views for Onboarding

class OnboardingStepViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OnboardingStep model.
    """
    queryset = OnboardingStep.objects.filter(is_active=True)
    serializer_class = OnboardingStepSerializer
    
    def get_queryset(self):
        """
        Filter steps by user type if specified.
        """
        queryset = super().get_queryset()
        user_type = self.request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset.order_by('user_type', 'order')


class UserOnboardingProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserOnboardingProgress model.
    """
    queryset = UserOnboardingProgress.objects.all()
    serializer_class = UserOnboardingProgressSerializer
    
    def get_queryset(self):
        """
        Filter progress by current user.
        """
        return UserOnboardingProgress.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def update_progress(self, request):
        """
        Update onboarding progress for a step.
        """
        serializer = OnboardingProgressUpdateSerializer(data=request.data)
        if serializer.is_valid():
            step_id = serializer.validated_data['step_id']
            action = serializer.validated_data['action']
            data = serializer.validated_data.get('data', {})
            
            try:
                step = OnboardingStep.objects.get(id=step_id, is_active=True)
            except OnboardingStep.DoesNotExist:
                return Response(
                    {'error': 'Step not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user has access to this step
            if step.user_type != request.user.user_type:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get or create progress record
            progress, created = UserOnboardingProgress.objects.get_or_create(
                user=request.user,
                step=step,
                defaults={'status': UserOnboardingProgress.Status.PENDING}
            )
            
            # Perform action
            if action == 'start':
                progress.mark_started()
            elif action == 'complete':
                # Validate step data if needed
                if step.step_type in [OnboardingStep.StepType.PROFILE_SETUP, OnboardingStep.StepType.ORGANISATION_SETUP]:
                    step_serializer = OnboardingStepDataSerializer(
                        data=data, 
                        context={'step_type': step.step_type}
                    )
                    if not step_serializer.is_valid():
                        return Response(
                            step_serializer.errors, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                progress.mark_completed(data)
            elif action == 'skip':
                if step.is_required:
                    return Response(
                        {'error': 'This step is required and cannot be skipped'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                progress.mark_skipped()
            
            # Check if onboarding is complete
            session = request.user.onboarding_session
            next_step = session.get_next_step()
            
            if not next_step and session.status == OnboardingSession.Status.IN_PROGRESS:
                session.complete()
            
            return Response({
                'progress': UserOnboardingProgressSerializer(progress).data,
                'next_step_id': str(next_step.id) if next_step else None,
                'is_complete': session.is_completed,
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OnboardingSession model.
    """
    queryset = OnboardingSession.objects.all()
    serializer_class = OnboardingSessionSerializer
    
    def get_queryset(self):
        """
        Filter sessions by current user.
        """
        return OnboardingSession.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        Start onboarding session for the current user.
        """
        user = request.user
        
        # Check if user already has an active session
        try:
            session = user.onboarding_session
            if session.status == OnboardingSession.Status.COMPLETED:
                return Response(
                    {'error': 'Onboarding already completed'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif session.status == OnboardingSession.Status.IN_PROGRESS:
                return Response(
                    {'error': 'Onboarding already in progress'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except OnboardingSession.DoesNotExist:
            session = OnboardingSession.objects.create(user=user)
        
        # Start the session
        session.start()
        
        # Create progress records for all steps
        steps = OnboardingStep.objects.filter(
            user_type=user.user_type,
            is_active=True
        ).order_by('order')
        
        for step in steps:
            UserOnboardingProgress.objects.get_or_create(
                user=user,
                step=step,
                defaults={'status': UserOnboardingProgress.Status.PENDING}
            )
        
        return Response(OnboardingSessionSerializer(session).data)
    
    @action(detail=False, methods=['post'])
    def abandon(self, request):
        """
        Abandon onboarding session for the current user.
        """
        try:
            session = request.user.onboarding_session
            session.abandon()
            return Response({'message': 'Onboarding session abandoned'})
        except OnboardingSession.DoesNotExist:
            return Response(
                {'error': 'No onboarding session found'}, 
                status=status.HTTP_404_NOT_FOUND
            )