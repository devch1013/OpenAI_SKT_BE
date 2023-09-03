from django.urls import path, include
from .views import *

urlpatterns = [
    path("", Projects.as_view()),
    path("<int:project_id>/recent", RecentDraft.as_view()),
    path("<int:project_id>/table", TableView.as_view()),
    path("<int:project_id>/suggestion/queue", SuggestionQueueView.as_view()),
    path("<int:project_id>/draft", DraftView.as_view()),
    path("<int:project_id>", SingleProject.as_view()),
    path("test", test),
]
