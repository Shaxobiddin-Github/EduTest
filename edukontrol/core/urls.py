from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SchoolViewSet, StudentViewSet, TestViewSet,
    QuestionViewSet, AnswerViewSet, ScoreViewSet, RatingViewSet, 
    top_10_students, school_ranking, district_ranking, region_ranking, nation_ranking,
    school_internal_scores, top_10_schools
)

router = DefaultRouter()
router.register(r'schools', SchoolViewSet)
router.register(r'students', StudentViewSet)
router.register(r'tests', TestViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'answers', AnswerViewSet)
router.register(r'scores', ScoreViewSet)
router.register(r'ratings', RatingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('top-10/<str:level>/', top_10_students, name='top_10_students'),
    path('school-ranking/<str:level>/', school_ranking, name='school_ranking'),
    path('district-ranking/', district_ranking, name='district_ranking'),
    path('region-ranking/', region_ranking, name='region_ranking'),
    path('nation-ranking/', nation_ranking, name='nation_ranking'),
    path('school-internal-scores/<int:school_id>/<str:test_type>/', school_internal_scores, name='school_internal_scores'),
    path('top-10-schools/<str:level>/', top_10_schools, name='top_10_schools'),
]
