from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # Web Dashboard & Interactive Studio
    path('', include('apps.dashboard.urls')),

    # REST API Domains
    path('api/erp/', include('apps.erp_connector.urls')),
    path('api/warehouse/', include('apps.data_warehouse.urls')),
    path('api/calculation/', include('apps.calculation_engine.urls')),

    # OpenAPI 3.0 & Interactive Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
