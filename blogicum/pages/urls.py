from django.urls import path

from . import views

app_name = "pages"
urlpatterns = [
    path("about/", views.AboutListView.as_view(), name="about"),
    path("rules/", views.RulesListView.as_view(), name="rules"),
]
