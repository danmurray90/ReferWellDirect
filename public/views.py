"""
Public views for ReferWell Direct landing page and role-specific pages.
"""
from django.shortcuts import render
from django.views.decorators.cache import cache_page


@cache_page(60 * 15)  # Cache for 15 minutes
def landing_page(request):
    """
    Public landing page with role sections and CTAs.
    """
    context = {
        "title": "ReferWell Direct - Intelligent Referral Matching",
        "description": "Connect patients with the right mental health professionals through intelligent matching",
    }
    return render(request, "public/landing.html", context)


@cache_page(60 * 15)  # Cache for 15 minutes
def for_gps(request):
    """
    GP-specific landing page with benefits and CTA.
    """
    context = {
        "title": "For GPs - ReferWell Direct",
        "description": "Streamline your mental health referrals with intelligent matching",
        "role": "gp",
        "benefits": [
            "Intelligent matching reduces referral time",
            "Access to verified psychologists",
            "Real-time availability and capacity tracking",
            "Automated follow-up and appointment scheduling",
            "Comprehensive audit trail for compliance",
        ],
        "cta_text": "Get Started",
        "cta_url": "/onboarding/gp/start/",
    }
    return render(request, "public/role_page.html", context)


@cache_page(60 * 15)  # Cache for 15 minutes
def for_psychologists(request):
    """
    Psychologist-specific landing page with benefits and CTA.
    """
    context = {
        "title": "For Psychologists - ReferWell Direct",
        "description": "Connect with patients who need your expertise",
        "role": "psychologist",
        "benefits": [
            "Receive referrals matched to your specialisms",
            "Flexible scheduling and capacity management",
            "Direct communication with referring GPs",
            "Professional development opportunities",
            "Streamlined administrative processes",
        ],
        "cta_text": "Join Our Network",
        "cta_url": "/onboarding/psych/start/",
    }
    return render(request, "public/role_page.html", context)


@cache_page(60 * 15)  # Cache for 15 minutes
def for_patients(request):
    """
    Patient-specific landing page with benefits and CTA.
    """
    context = {
        "title": "For Patients - ReferWell Direct",
        "description": "Find the right mental health support for you",
        "role": "patient",
        "benefits": [
            "Quick access to verified mental health professionals",
            "Matched to your specific needs and preferences",
            "Flexible appointment options (in-person or remote)",
            "Transparent process with clear communication",
            "Support throughout your mental health journey",
        ],
        "cta_text": "Start Your Journey",
        "cta_url": "/self-referral/start/",
    }
    return render(request, "public/role_page.html", context)
