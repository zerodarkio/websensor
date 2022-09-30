from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
import capture.views

urlpatterns = [
    
    path('173rgyqwefiqwrt7219231r/', admin.site.urls),
    path('', include('capture.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'capture.views.handler404'
handler500 = 'capture.views.handler500'
