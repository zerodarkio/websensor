from django.urls import path, re_path
from django.conf.urls import include, url
from django.views.generic.base import RedirectView
from . import views


urlpatterns = [
    path('', views.index, name='index'),

]
