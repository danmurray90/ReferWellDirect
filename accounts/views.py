"""
Views for the accounts app.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .models import (
    OnboardingSession,
    OnboardingStep,
    Organisation,
    User,
    UserOnboardingProgress,
    UserOrganisation,
    VerificationStatus,
)
from .serializers import (
    OnboardingProgressUpdateSerializer,
    OnboardingSessionSerializer,
    OnboardingStepDataSerializer,
    OnboardingStepSerializer,
    OrganisationSerializer,
    UserOnboardingProgressSerializer,
    UserSerializer,
)


def home(request):
    """
    Home page view.
    """
    context = {
        "title": "ReferWell Direct",
        "description": "Intelligent referral matching for mental health services",
    }
    return render(request, "accounts/home.html", context)


@login_required
def dashboard(request):
    """
    User dashboard view.
    """
    user = request.user
    context = {
        "title": f"Dashboard - {user.get_full_name()}",
        "user": user,
        "user_type": user.get_user_type_display(),
    }
    return render(request, "accounts/dashboard.html", context)


@csrf_protect
@require_http_methods(["GET", "POST"])
def signin(request):
    """
    User sign in view.
    """
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if email and password:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get("next", "referrals:dashboard")
                return redirect(next_url)
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Please provide both email and password.")

    return render(request, "accounts/signin.html")


@require_http_methods(["POST"])
def signout(request):
    """
    User sign out view.
    """
    logout(request)
    messages.success(request, "You have been signed out successfully.")
    return redirect("accounts:home")


@csrf_protect
@require_http_methods(["GET", "POST"])
def signup(request):
    """
    User sign up view.
    """
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        user_type = request.POST.get("user_type")

        if all([email, password, first_name, last_name, user_type]):
            try:
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    user_type=user_type,
                )
                login(request, user)
                messages.success(request, "Account created successfully!")
                return redirect("accounts:dashboard")
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, "accounts/signup.html")


@login_required
def profile(request):
    """
    User profile view.
    """
    user = request.user
    context = {
        "title": f"Profile - {user.get_full_name()}",
        "user": user,
    }
    return render(request, "accounts/profile.html", context)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=["get"])
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

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Search organisations by name or postcode.
        """
        query = request.GET.get("q", "")
        if query:
            organisations = self.queryset.filter(
                models.Q(name__icontains=query) | models.Q(postcode__icontains=query)
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
        user=user, defaults={"status": OnboardingSession.Status.NOT_STARTED}
    )

    if session.status == OnboardingSession.Status.COMPLETED:
        messages.info(request, "You have already completed the onboarding process.")
        return redirect("accounts:dashboard")

    # Create progress records for all steps if they don't exist
    steps = OnboardingStep.objects.filter(
        user_type=user.user_type, is_active=True
    ).order_by("order")

    # Check if there are any onboarding steps for this user type
    if not steps.exists():
        messages.warning(
            request,
            "No onboarding steps are configured for your user type. Please contact an administrator.",
        )
        return redirect("accounts:dashboard")

    for step in steps:
        UserOnboardingProgress.objects.get_or_create(
            user=user,
            step=step,
            defaults={"status": UserOnboardingProgress.Status.PENDING},
        )

    # Start the session if not already started
    if session.status == OnboardingSession.Status.NOT_STARTED:
        session.start()

    # Check if current_step is set (should be after start())
    if not session.current_step:
        messages.error(
            request,
            "Unable to determine the next onboarding step. Please contact an administrator.",
        )
        return redirect("accounts:dashboard")

    return redirect("accounts:onboarding_step", step_id=session.current_step.id)


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
        return redirect("accounts:dashboard")

    # Get or create progress record
    progress, created = UserOnboardingProgress.objects.get_or_create(
        user=user, step=step, defaults={"status": UserOnboardingProgress.Status.PENDING}
    )

    # Mark as started if not already
    if progress.status == UserOnboardingProgress.Status.PENDING:
        progress.mark_started()

    # For completion steps, automatically mark as completed when viewed
    if (
        step.step_type == OnboardingStep.StepType.COMPLETION
        and progress.status == UserOnboardingProgress.Status.IN_PROGRESS
    ):
        progress.mark_completed()

    # Get all steps for this user type for progress indicator
    all_steps = OnboardingStep.objects.filter(
        user_type=user.user_type, is_active=True
    ).order_by("order")

    # Get next step
    session = user.onboarding_session
    next_step = session.get_next_step()

    # Get previous step
    previous_step = None
    if step.order > 1:
        try:
            previous_step = (
                all_steps.filter(order__lt=step.order).order_by("-order").first()
            )
        except OnboardingStep.DoesNotExist:
            previous_step = None

    # Calculate progress percentage
    total_steps = all_steps.count()
    completed_steps = user.onboarding_progress.filter(
        status=UserOnboardingProgress.Status.COMPLETED
    ).count()
    progress_percentage = (
        int((completed_steps / total_steps) * 100) if total_steps > 0 else 100
    )

    # Get progress records for all steps
    progress_records = user.onboarding_progress.filter(step__in=all_steps)
    progress_by_step = {p.step_id: p for p in progress_records}

    # Create enhanced steps list with status information
    enhanced_steps = []
    for step_obj in all_steps:
        step_progress = progress_by_step.get(step_obj.id)
        if step_progress:
            step_status = step_progress.status
        else:
            step_status = UserOnboardingProgress.Status.PENDING

        enhanced_steps.append(
            {
                "step": step_obj,
                "is_current": step_obj.id == step.id,
                "status": step_status,
                "order": step_obj.order,
                "name": step_obj.name,
            }
        )

    context = {
        "title": f"Onboarding - {step.name}",
        "step": step,
        "progress": progress,
        "user": user,
        "all_steps": enhanced_steps,
        "next_step": next_step,
        "previous_step": previous_step,
        "progress_percentage": progress_percentage,
        "total_steps": total_steps,
    }

    # Add step-specific context
    if step.step_type == OnboardingStep.StepType.PROFILE_SETUP:
        context["form_data"] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "date_of_birth": user.date_of_birth,
        }
    elif step.step_type == OnboardingStep.StepType.ORGANISATION_SETUP:
        # Get user's organisations
        user_orgs = user.user_organisations.filter(is_active=True)
        context["user_organisations"] = user_orgs
    elif step.step_type == OnboardingStep.StepType.PREFERENCES:
        context["form_data"] = {
            "preferred_language": user.preferred_language,
            "timezone": user.timezone,
        }

    return render(request, f"accounts/onboarding/{step.step_type}.html", context)


@login_required
def onboarding_complete_step(request, step_id):
    """
    Complete a specific onboarding step.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = request.user
    step = get_object_or_404(OnboardingStep, id=step_id, is_active=True)

    # Check if user has access to this step
    if step.user_type != user.user_type:
        return JsonResponse({"error": "Access denied"}, status=403)

    # Get progress record
    try:
        progress = UserOnboardingProgress.objects.get(user=user, step=step)
    except UserOnboardingProgress.DoesNotExist:
        return JsonResponse({"error": "Progress record not found"}, status=404)

    # Validate and process step data
    step_data = {}

    if step.step_type == OnboardingStep.StepType.PROFILE_SETUP:
        # Update user profile
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.phone = request.POST.get("phone", user.phone)
        if request.POST.get("date_of_birth"):
            user.date_of_birth = request.POST.get("date_of_birth")
        user.save()

        step_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "date_of_birth": str(user.date_of_birth) if user.date_of_birth else None,
        }

    elif step.step_type == OnboardingStep.StepType.ORGANISATION_SETUP:
        # Handle organisation setup
        org_name = request.POST.get("organisation_name")
        org_type = request.POST.get("organisation_type")

        if org_name and org_type:
            # Create or find organisation
            organisation, created = Organisation.objects.get_or_create(
                name=org_name,
                defaults={
                    "organisation_type": org_type,
                    "created_by": user,
                },
            )

            # Create user-organisation relationship
            UserOrganisation.objects.get_or_create(
                user=user,
                organisation=organisation,
                defaults={
                    "role": UserOrganisation.Role.OWNER
                    if created
                    else UserOrganisation.Role.MEMBER,
                    "created_by": user,
                },
            )

            step_data = {
                "organisation_name": org_name,
                "organisation_type": org_type,
                "organisation_id": str(organisation.id),
            }

    elif step.step_type == OnboardingStep.StepType.PREFERENCES:
        # Update user preferences
        user.preferred_language = request.POST.get(
            "preferred_language", user.preferred_language
        )
        user.timezone = request.POST.get("timezone", user.timezone)
        user.save()

        step_data = {
            "preferred_language": user.preferred_language,
            "timezone": user.timezone,
        }

    # Mark step as completed
    progress.mark_completed(step_data)

    # Check if onboarding is complete
    session = user.onboarding_session
    next_step = session.get_next_step()

    if next_step:
        # Update current step and redirect to next step
        session.update_current_step()
        return redirect("accounts:onboarding_step", step_id=next_step.id)
    else:
        # Complete onboarding
        session.complete()
        messages.success(
            request, "Congratulations! You have completed the onboarding process."
        )
        return redirect("accounts:dashboard")


@login_required
def onboarding_skip_step(request, step_id):
    """
    Skip a specific onboarding step.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user = request.user
    step = get_object_or_404(OnboardingStep, id=step_id, is_active=True)

    # Check if user has access to this step
    if step.user_type != user.user_type:
        return JsonResponse({"error": "Access denied"}, status=403)

    # Get progress record
    try:
        progress = UserOnboardingProgress.objects.get(user=user, step=step)
    except UserOnboardingProgress.DoesNotExist:
        return JsonResponse({"error": "Progress record not found"}, status=404)

    # Skip step if it's not required
    if step.is_required:
        return JsonResponse(
            {"error": "This step is required and cannot be skipped"}, status=400
        )

    # Mark step as skipped
    progress.mark_skipped()

    # Check if onboarding is complete
    session = user.onboarding_session
    next_step = session.get_next_step()

    if next_step:
        # Update current step and redirect to next step
        session.update_current_step()
        return redirect("accounts:onboarding_step", step_id=next_step.id)
    else:
        # Complete onboarding
        session.complete()
        messages.success(request, "You have completed the onboarding process.")
        return redirect("accounts:dashboard")


@login_required
def onboarding_progress(request):
    """
    Get onboarding progress for the current user.
    """
    user = request.user

    try:
        session = user.onboarding_session
    except OnboardingSession.DoesNotExist:
        return JsonResponse({"error": "No onboarding session found"}, status=404)

    # Get all progress records
    progress_records = UserOnboardingProgress.objects.filter(user=user).select_related(
        "step"
    )

    # Calculate progress
    total_steps = OnboardingStep.objects.filter(
        user_type=user.user_type, is_active=True
    ).count()

    completed_steps = progress_records.filter(
        status=UserOnboardingProgress.Status.COMPLETED
    ).count()

    progress_percentage = (
        int((completed_steps / total_steps) * 100) if total_steps > 0 else 100
    )

    # Get current step
    current_step = session.current_step

    # Get all steps with their status
    steps = []
    for step in OnboardingStep.objects.filter(
        user_type=user.user_type, is_active=True
    ).order_by("order"):
        try:
            progress = progress_records.get(step=step)
            step_status = progress.status
        except UserOnboardingProgress.DoesNotExist:
            step_status = UserOnboardingProgress.Status.PENDING

        steps.append(
            {
                "id": str(step.id),
                "name": step.name,
                "step_type": step.step_type,
                "order": step.order,
                "is_required": step.is_required,
                "status": step_status,
                "is_current": current_step and step.id == current_step.id,
            }
        )

    return JsonResponse(
        {
            "session": {
                "id": str(session.id),
                "status": session.status,
                "progress_percentage": progress_percentage,
                "current_step_id": str(current_step.id) if current_step else None,
            },
            "steps": steps,
        }
    )


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
        user_type = self.request.query_params.get("user_type")
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset.order_by("user_type", "order")


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

    @action(detail=False, methods=["post"])
    def update_progress(self, request):
        """
        Update onboarding progress for a step.
        """
        serializer = OnboardingProgressUpdateSerializer(data=request.data)
        if serializer.is_valid():
            step_id = serializer.validated_data["step_id"]
            action = serializer.validated_data["action"]
            data = serializer.validated_data.get("data", {})

            try:
                step = OnboardingStep.objects.get(id=step_id, is_active=True)
            except OnboardingStep.DoesNotExist:
                return Response(
                    {"error": "Step not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Check if user has access to this step
            if step.user_type != request.user.user_type:
                return Response(
                    {"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN
                )

            # Get or create progress record
            progress, created = UserOnboardingProgress.objects.get_or_create(
                user=request.user,
                step=step,
                defaults={"status": UserOnboardingProgress.Status.PENDING},
            )

            # Perform action
            if action == "start":
                progress.mark_started()
            elif action == "complete":
                # Validate step data if needed
                if step.step_type in [
                    OnboardingStep.StepType.PROFILE_SETUP,
                    OnboardingStep.StepType.ORGANISATION_SETUP,
                ]:
                    step_serializer = OnboardingStepDataSerializer(
                        data=data, context={"step_type": step.step_type}
                    )
                    if not step_serializer.is_valid():
                        return Response(
                            step_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )

                progress.mark_completed(data)
            elif action == "skip":
                if step.is_required:
                    return Response(
                        {"error": "This step is required and cannot be skipped"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                progress.mark_skipped()

            # Check if onboarding is complete
            session = request.user.onboarding_session
            next_step = session.get_next_step()

            if not next_step and session.status == OnboardingSession.Status.IN_PROGRESS:
                session.complete()

            return Response(
                {
                    "progress": UserOnboardingProgressSerializer(progress).data,
                    "next_step_id": str(next_step.id) if next_step else None,
                    "is_complete": session.is_completed,
                }
            )

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

    @action(detail=False, methods=["post"])
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
                    {"error": "Onboarding already completed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif session.status == OnboardingSession.Status.IN_PROGRESS:
                return Response(
                    {"error": "Onboarding already in progress"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except OnboardingSession.DoesNotExist:
            session = OnboardingSession.objects.create(user=user)

        # Start the session
        session.start()

        # Create progress records for all steps
        steps = OnboardingStep.objects.filter(
            user_type=user.user_type, is_active=True
        ).order_by("order")

        for step in steps:
            UserOnboardingProgress.objects.get_or_create(
                user=user,
                step=step,
                defaults={"status": UserOnboardingProgress.Status.PENDING},
            )

        return Response(OnboardingSessionSerializer(session).data)

    @action(detail=False, methods=["post"])
    def abandon(self, request):
        """
        Abandon onboarding session for the current user.
        """
        try:
            session = request.user.onboarding_session
            session.abandon()
            return Response({"message": "Onboarding session abandoned"})
        except OnboardingSession.DoesNotExist:
            return Response(
                {"error": "No onboarding session found"},
                status=status.HTTP_404_NOT_FOUND,
            )


# New role-based onboarding views


@csrf_protect
@require_http_methods(["GET", "POST"])
def gp_onboarding_start(request):
    """
    GP onboarding start view with verification status.
    """
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        # Handle GP signup form
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")

        # Organisation details
        org_name = request.POST.get("org_name")
        org_type = request.POST.get("org_type")
        org_email = request.POST.get("org_email")
        org_phone = request.POST.get("org_phone")
        org_address = request.POST.get("org_address")
        org_city = request.POST.get("org_city")
        org_postcode = request.POST.get("org_postcode")

        # Professional details
        gmc_number = request.POST.get("gmc_number")

        if email and password and first_name and last_name:
            try:
                # Create user
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    user_type=User.UserType.GP,
                    is_verified=False,  # Will be verified by admin
                )

                # Create organisation if provided
                if org_name:
                    organisation = Organisation.objects.create(
                        name=org_name,
                        organisation_type=org_type
                        or Organisation.OrganisationType.GP_PRACTICE,
                        email=org_email,
                        phone=org_phone,
                        address_line_1=org_address,
                        city=org_city,
                        postcode=org_postcode,
                        created_by=user,
                    )

                    # Link user to organisation
                    UserOrganisation.objects.create(
                        user=user,
                        organisation=organisation,
                        role=UserOrganisation.Role.OWNER,
                        created_by=user,
                    )

                # Create verification status
                VerificationStatus.objects.create(
                    user=user,
                    status=VerificationStatus.Status.PENDING,
                    notes=f"GMC Number: {gmc_number}" if gmc_number else "",
                )

                # Authenticate and login user
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    messages.success(
                        request,
                        "Account created successfully! Your account is pending verification. "
                        "You'll be notified once verified.",
                    )
                    return redirect("accounts:verification_pending")

            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, "accounts/onboarding/gp_signup.html")


@csrf_protect
@require_http_methods(["GET", "POST"])
def psych_onboarding_start(request):
    """
    Psychologist onboarding start view with verification status.
    """
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        # Handle Psychologist signup form
        email = request.POST.get("email")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        phone = request.POST.get("phone")

        # Professional details
        bio = request.POST.get("bio")
        specialisms = request.POST.getlist("specialisms")
        modalities = request.POST.getlist("modalities")
        languages = request.POST.getlist("languages")

        # Service preferences
        nhs_provider = request.POST.get("nhs_provider") == "on"
        private_provider = request.POST.get("private_provider") == "on"

        # Location
        address_line_1 = request.POST.get("address_line_1")
        city = request.POST.get("city")
        postcode = request.POST.get("postcode")

        if email and password and first_name and last_name:
            try:
                # Create user
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    user_type=User.UserType.PSYCHOLOGIST,
                    is_verified=False,  # Will be verified by admin
                )

                # Create verification status
                VerificationStatus.objects.create(
                    user=user,
                    status=VerificationStatus.Status.PENDING,
                    notes=f"Bio: {bio}\nSpecialisms: {', '.join(specialisms)}\nModalities: {', '.join(modalities)}",
                )

                # Authenticate and login user
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    messages.success(
                        request,
                        "Account created successfully! Your account is pending verification. "
                        "You'll be notified once verified.",
                    )
                    return redirect("accounts:verification_pending")

            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, "accounts/onboarding/psych_signup.html")


@login_required
def verification_pending(request):
    """
    Show verification pending page for unverified users.
    """
    user = request.user

    # Check if user needs verification
    if user.user_type in [User.UserType.GP, User.UserType.PSYCHOLOGIST]:
        try:
            verification_status = user.verification_status
            if verification_status.is_pending:
                context = {
                    "title": "Verification Pending",
                    "user": user,
                    "verification_status": verification_status,
                }
                return render(request, "accounts/verification_pending.html", context)
        except:
            pass

    # If verified or doesn't need verification, redirect to dashboard
    return redirect("accounts:dashboard")


@login_required
def gp_create_patient(request):
    """
    GP creates a new patient profile.
    """
    if not request.user.is_gp:
        messages.error(request, "Access denied. This page is for GPs only.")
        return redirect("accounts:dashboard")

    # Check if GP is verified
    try:
        if request.user.verification_status.is_pending:
            messages.error(
                request,
                "Your account is pending verification. Please wait for admin approval.",
            )
            return redirect("accounts:verification_pending")
    except:
        pass

    if request.method == "POST":
        # Handle patient creation form
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        date_of_birth = request.POST.get("date_of_birth")
        nhs_number = request.POST.get("nhs_number")

        if first_name and last_name:
            try:
                from referrals.models import PatientProfile

                patient_profile = PatientProfile.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    date_of_birth=date_of_birth if date_of_birth else None,
                    nhs_number=nhs_number,
                    created_by=request.user,
                )

                messages.success(
                    request,
                    f"Patient profile created for {patient_profile.get_full_name()}",
                )
                return redirect("referrals:create")

            except Exception as e:
                messages.error(request, f"Error creating patient profile: {str(e)}")
        else:
            messages.error(request, "Please provide at least first name and last name.")

    return render(request, "accounts/gp_create_patient.html")


@login_required
def gp_invite_patient(request, patient_id):
    """
    GP generates invite link for patient to claim their profile.
    """
    if not request.user.is_gp:
        messages.error(request, "Access denied. This page is for GPs only.")
        return redirect("accounts:dashboard")

    try:
        import secrets
        from datetime import timedelta

        from django.utils import timezone

        from referrals.models import PatientProfile

        from .models import PatientClaimInvite

        patient_profile = PatientProfile.objects.get(
            id=patient_id, created_by=request.user
        )

        if request.method == "POST":
            email = request.POST.get("email")
            if email:
                # Generate secure token
                token = secrets.token_urlsafe(32)

                # Create invite (expires in 7 days)
                invite = PatientClaimInvite.objects.create(
                    token=token,
                    patient_profile=patient_profile,
                    email=email,
                    expires_at=timezone.now() + timedelta(days=7),
                    created_by=request.user,
                )

                # Generate claim URL
                claim_url = request.build_absolute_uri(f"/claim/{token}/")

                messages.success(request, f"Invite created for {email}")
                context = {
                    "title": "Patient Invite Created",
                    "patient_profile": patient_profile,
                    "invite": invite,
                    "claim_url": claim_url,
                }
                return render(request, "accounts/gp_invite_success.html", context)
            else:
                messages.error(request, "Please provide an email address.")

        context = {
            "title": "Invite Patient",
            "patient_profile": patient_profile,
        }
        return render(request, "accounts/gp_invite_patient.html", context)

    except PatientProfile.DoesNotExist:
        messages.error(request, "Patient profile not found.")
        return redirect("accounts:dashboard")


@csrf_protect
@require_http_methods(["GET", "POST"])
def patient_claim(request, token):
    """
    Patient claims their profile using secure token.
    """
    try:
        from referrals.models import PatientProfile

        from .models import PatientClaimInvite

        invite = PatientClaimInvite.objects.get(token=token)

        if not invite.is_valid:
            messages.error(
                request, "This invite link has expired or has already been used."
            )
            return redirect("public:landing")

        if request.method == "POST":
            # Handle account creation/linking
            email = request.POST.get("email")
            password = request.POST.get("password")
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")

            if email and password and first_name and last_name:
                try:
                    # Create user account
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        user_type=User.UserType.PATIENT,
                        is_verified=True,  # Patients don't need verification
                    )

                    # Link patient profile to user
                    invite.patient_profile.link_to_user(user)

                    # Mark invite as used
                    invite.mark_used()

                    # Authenticate and login user
                    user = authenticate(request, username=email, password=password)
                    if user:
                        login(request, user)
                        messages.success(
                            request, "Account created and linked successfully!"
                        )
                        return redirect("accounts:dashboard")

                except Exception as e:
                    messages.error(request, f"Error creating account: {str(e)}")
            else:
                messages.error(request, "Please fill in all required fields.")

        context = {
            "title": "Claim Your Profile",
            "invite": invite,
            "patient_profile": invite.patient_profile,
        }
        return render(request, "accounts/patient_claim.html", context)

    except PatientClaimInvite.DoesNotExist:
        messages.error(request, "Invalid invite link.")
        return redirect("public:landing")
