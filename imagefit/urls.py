from django.conf.urls import url, re_path
from . import views

"""
Master URL using
  path('image', include('imagefit.urls')),
"""

urlpatterns = [
    url(
        r'^(?P<url>.*)/(?P<format>[,\w-]+)/(?P<path_name>[\w_-]*)/?$',
        views.resize,
        name="imagefit_resize"),
]
