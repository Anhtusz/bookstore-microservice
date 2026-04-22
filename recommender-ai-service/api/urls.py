from django.urls import path
from .views import (
    RecommendView,
    ChatView,
    PredictView,
    TrackEventView,
    TrackBatchView,
    PopularRecommendationsView,
    SuggestRecommendationsView,
    ByCategoryRecommendationsView,
    SessionRecommendationsView,
    ChatRecommendationsView,
)

urlpatterns = [
    path('recommend/', RecommendView.as_view(), name='recommend'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('predict/', PredictView.as_view(), name='predict'),
    path('track/', TrackEventView.as_view(), name='track-event'),
    path('track/batch/', TrackBatchView.as_view(), name='track-batch'),

    # Frontend-compatible recommendation routes
    path('recommendations/popular/', PopularRecommendationsView.as_view(), name='rec-popular'),
    path('recommendations/suggest/', SuggestRecommendationsView.as_view(), name='rec-suggest'),
    path('recommendations/by_category/', ByCategoryRecommendationsView.as_view(), name='rec-by-category'),
    path('recommendations/for_session/', SessionRecommendationsView.as_view(), name='rec-for-session'),
    path('recommendations/chat/', ChatRecommendationsView.as_view(), name='rec-chat'),
]
