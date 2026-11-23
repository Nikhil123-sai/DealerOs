
from django.contrib import admin
from django.urls import path

from reconcile.views import disagreements_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/disagreements/",
        disagreements_view,
        name="disagreements",
    ),
]
