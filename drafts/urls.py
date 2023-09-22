from django.urls import path, include
from .views.project_views import *
from .views.qna_views import *
from .views.draft_views import *
from .views.datasource_views import *
from .views.file_views import *

urlpatterns = [
    path("", Projects.as_view()),
    path("<int:project_id>/qna", QnAViews.as_view()),
    path("<int:project_id>/recent", RecentDraft.as_view()),
    # path("<int:project_id>/table", SuggestionView.as_view()),
    path("<int:project_id>/suggestion", SuggestionView.as_view()),
    path("<int:project_id>/suggestion/queue", SuggestionQueueView.as_view()),
    # path("<int:project_id>/draft/first", FirstDraftView.as_view()),
    # path("<int:project_id>/draft/test", DraftStreamingView.as_view()),
    path("<int:project_id>/draft", DraftView.as_view()),
    path("<int:project_id>/datasource", DataSourceView.as_view()),
    path("<int:project_id>", SingleProject.as_view()),
    # path("draft/<int:draft_id>/queue", DraftQueueView.as_view()),
    # path("draft/<int:draft_id>/table", DraftQueueView.as_view()),
    path("draft/<int:draft_id>/regenerate", RegenerateView.as_view()),
    path("draft/<int:draft_id>/download", DraftDownloadView.as_view()),
    path("draft/<int:draft_id>", SingleDraftView.as_view()),
    
    path("resource/<int:source_id>", DataSourceFileView.as_view()),
    path("profile_image", ProfileImageView.as_view()),
    
    
    path("test", api_test),
]
