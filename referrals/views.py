"""
Views for referrals app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Referral, Candidate, Appointment, Message, Task
from .serializers import ReferralSerializer, CandidateSerializer, AppointmentSerializer, MessageSerializer, TaskSerializer


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view.
    """
    template_name = 'referrals/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_gp:
            context['referrals'] = Referral.objects.filter(referrer=user).order_by('-created_at')[:10]
            context['pending_tasks'] = Task.objects.filter(assigned_to=user, is_completed=False).order_by('-due_at')[:5]
        elif user.is_patient:
            context['referrals'] = Referral.objects.filter(patient=user).order_by('-created_at')[:10]
            context['upcoming_appointments'] = Appointment.objects.filter(
                patient=user, 
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
            ).order_by('scheduled_at')[:5]
        elif user.is_psychologist:
            context['candidates'] = Candidate.objects.filter(psychologist=user).order_by('-created_at')[:10]
            context['upcoming_appointments'] = Appointment.objects.filter(
                psychologist=user,
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
            ).order_by('scheduled_at')[:5]
        elif user.is_admin:
            context['recent_referrals'] = Referral.objects.all().order_by('-created_at')[:10]
            context['pending_tasks'] = Task.objects.filter(is_completed=False).order_by('-due_at')[:10]
        
        return context


class CreateReferralView(LoginRequiredMixin, TemplateView):
    """
    Create referral form view.
    """
    template_name = 'referrals/create_referral.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referral'] = Referral()
        return context
    
    def post(self, request, *args, **kwargs):
        # Handle form submission
        referral_data = {
            'referrer': request.user,
            'patient': request.user,  # For MVP, assume referrer is also patient
            'presenting_problem': request.POST.get('presenting_problem'),
            'clinical_notes': request.POST.get('clinical_notes', ''),
            'service_type': request.POST.get('service_type', Referral.ServiceType.NHS),
            'modality': request.POST.get('modality', Referral.Modality.MIXED),
            'priority': request.POST.get('priority', Referral.Priority.MEDIUM),
            'max_distance_km': int(request.POST.get('max_distance_km', 50)),
            'preferred_language': request.POST.get('preferred_language', 'en'),
            'created_by': request.user,
        }
        
        try:
            referral = Referral.objects.create(**referral_data)
            messages.success(request, f'Referral {referral.referral_id} created successfully!')
            return redirect('referrals:referral_detail', pk=referral.pk)
        except Exception as e:
            messages.error(request, f'Error creating referral: {str(e)}')
            return self.get(request, *args, **kwargs)


class ReferralListView(LoginRequiredMixin, ListView):
    """
    List view for referrals.
    """
    model = Referral
    template_name = 'referrals/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user).order_by('-created_at')
        elif user.is_patient:
            return Referral.objects.filter(patient=user).order_by('-created_at')
        elif user.is_admin:
            return Referral.objects.all().order_by('-created_at')
        else:
            return Referral.objects.none()


class ReferralDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a specific referral.
    """
    model = Referral
    template_name = 'referrals/referral_detail.html'
    context_object_name = 'referral'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user)
        elif user.is_patient:
            return Referral.objects.filter(patient=user)
        elif user.is_admin:
            return Referral.objects.all()
        else:
            return Referral.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referral = self.get_object()
        context['candidates'] = referral.candidates.all().order_by('-final_score')
        context['appointments'] = referral.appointments.all().order_by('-scheduled_at')
        context['messages'] = referral.messages.all().order_by('-created_at')
        return context


class ShortlistView(LoginRequiredMixin, TemplateView):
    """
    Shortlist view for referral candidates.
    """
    template_name = 'referrals/shortlist.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        referral_id = self.kwargs.get('referral_id')
        referral = get_object_or_404(Referral, id=referral_id)
        
        # Check permissions
        user = self.request.user
        if not (user.is_gp and referral.referrer == user) and not user.is_admin:
            raise PermissionDenied
        
        context['referral'] = referral
        context['candidates'] = referral.candidates.filter(
            status__in=[Candidate.Status.SHORTLISTED, Candidate.Status.INVITED]
        ).order_by('-final_score')
        
        return context


# API Views
class ReferralListAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating referrals.
    """
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user)
        elif user.is_patient:
            return Referral.objects.filter(patient=user)
        elif user.is_admin:
            return Referral.objects.all()
        else:
            return Referral.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(referrer=self.request.user, created_by=self.request.user)


class ReferralDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific referral.
    """
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_gp:
            return Referral.objects.filter(referrer=user)
        elif user.is_patient:
            return Referral.objects.filter(patient=user)
        elif user.is_admin:
            return Referral.objects.all()
        else:
            return Referral.objects.none()


class CandidateListAPIView(generics.ListAPIView):
    """
    API view for listing candidates for a referral.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        referral_id = self.kwargs.get('referral_id')
        return Candidate.objects.filter(referral_id=referral_id).order_by('-final_score')


class CandidateDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating a specific candidate.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Candidate.objects.all()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_referral(request, referral_id):
    """
    API endpoint to submit a referral for matching.
    """
    try:
        referral = Referral.objects.get(id=referral_id)
        
        # Check permissions
        if not (request.user.is_gp and referral.referrer == request.user) and not request.user.is_admin:
            return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)
        
        if referral.status != Referral.Status.DRAFT:
            return Response({'error': 'Referral is not in draft status'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update status
        referral.status = Referral.Status.SUBMITTED
        from django.utils import timezone
        referral.submitted_at = timezone.now()
        referral.save()
        
        # Trigger matching process (placeholder)
        # This would typically trigger a Celery task
        
        return Response({'message': 'Referral submitted successfully'}, status=status.HTTP_200_OK)
        
    except Referral.DoesNotExist:
        return Response({'error': 'Referral not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_to_invitation(request, candidate_id):
    """
    API endpoint for psychologists to respond to invitations.
    """
    try:
        candidate = Candidate.objects.get(id=candidate_id)
        
        # Check permissions
        if candidate.psychologist != request.user:
            return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)
        
        if candidate.status != Candidate.Status.INVITED:
            return Response({'error': 'Candidate is not in invited status'}, status=status.HTTP_400_BAD_REQUEST)
        
        response = request.data.get('response')  # 'accepted' or 'declined'
        notes = request.data.get('notes', '')
        
        if response == 'accepted':
            candidate.status = Candidate.Status.ACCEPTED
        elif response == 'declined':
            candidate.status = Candidate.Status.DECLINED
        else:
            return Response({'error': 'Invalid response'}, status=status.HTTP_400_BAD_REQUEST)
        
        candidate.response_notes = notes
        from django.utils import timezone
        candidate.responded_at = timezone.now()
        candidate.save()
        
        return Response({'message': 'Response recorded successfully'}, status=status.HTTP_200_OK)
        
    except Candidate.DoesNotExist:
        return Response({'error': 'Candidate not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
