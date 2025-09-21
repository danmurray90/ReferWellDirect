"""
URL configuration for ReferWell Direct project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/v1/', include('referwell.api_urls')),
    
    # App-specific URLs
    path('accounts/', include('accounts.urls')),
    path('referrals/', include('referrals.urls')),
    path('catalogue/', include('catalogue.urls')),
    path('matching/', include('matching.urls')),
    path('inbox/', include('inbox.urls')),
    path('payments/', include('payments.urls')),
    path('ops/', include('ops.urls')),
    
    # Root redirect to accounts home
    path('', RedirectView.as_view(url='/accounts/', permanent=False)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Admin site customization
admin.site.site_header = "ReferWell Direct Administration"
admin.site.site_title = "ReferWell Direct Admin"
admin.site.index_title = "Welcome to ReferWell Direct Administration"
