from django.urls import path
from .views import (
    SessionView,
    DocumentUploadView,
    ChatView,
    MessagesHistoryView,
    FeedbackView,
    CollegePolicyView
)

urlpatterns = [
    path('sessions', SessionView.as_view(), name='sessions-create'),
    path('sessions/<uuid:session_id>', SessionView.as_view(), name='sessions-delete'),
    path('sessions/<uuid:session_id>/messages', MessagesHistoryView.as_view(), name='messages-history'),
    path('documents', DocumentUploadView.as_view(), name='documents-upload'),
    path('documents/<uuid:document_id>', DocumentUploadView.as_view(), name='documents-detail'),
    path('chat', ChatView.as_view(), name='chat'),
    path('feedback', FeedbackView.as_view(), name='feedback'),
    path('college-policy', CollegePolicyView.as_view(), name='college-policy'),
    path('reset-to-policy', CollegePolicyView.as_view(), name='reset-to-policy'),
]
