from rest_framework import viewsets
from .models import School, Student, Test, Question, Answer, Score, Rating
from .serializers import (
    SchoolSerializer, StudentSerializer, TestSerializer,
    QuestionSerializer, AnswerSerializer, ScoreSerializer, RatingSerializer
)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Score, Rating, Student
from django.db.models import Sum




class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer









@api_view(['POST'])
def update_ratings(request):
    """
    Barcha o‘quvchilar uchun umumiy reytingni hisoblaydi va `Rating` modelida saqlaydi.
    """
    students = Student.objects.all()
    updated = 0

    for student in students:
        # Chorak testlar (koeffitsiyent: 1x)
        quarter_scores = Score.objects.filter(
            student=student,
            test__test_type='quarter'
        ).aggregate(total=Sum('score'))['total'] or 0

        # Yillik testlar (koeffitsiyent: 2x)
        annual_scores = Score.objects.filter(
            student=student,
            test__test_type='annual'
        ).aggregate(total=Sum('score'))['total'] or 0
        annual_scores *= 2

        # Final (bitiruv) testlar (koeffitsiyent: 3x, faqat 9 va 11-sinflar uchun)
        final_scores = 0
        if student.grade in [9, 11]:
            final_scores = Score.objects.filter(
                student=student,
                test__test_type='final'
            ).aggregate(total=Sum('score'))['total'] or 0
            final_scores *= 3

        total_score = quarter_scores + annual_scores + final_scores

        # Ratingni yangilash yoki yaratish
        Rating.objects.update_or_create(
            student=student,
            defaults={
                'school': student.school,
                'total_score': total_score
            }
        )
        updated += 1

    return Response({
        "status": "success",
        "message": f"{updated} ta o‘quvchi reytingi yangilandi."
    })


from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Rating, Student
from django.db.models import F

@api_view(['GET'])
def top_10_students(request, level):
    """
    Har xil darajadagi (maktab, tuman, viloyat, respublika) eng yaxshi 10 o‘quvchini ko‘rsatadi.
    """
    if level not in ['school', 'district', 'region', 'nation']:
        return Response({"status": "error", "message": "Noto'g'ri daraja!"}, status=400)

    top_students = Rating.objects.filter(level=level).order_by('-total_score')[:10]

    data = []
    for rating in top_students:
        student = rating.student
        data.append({
            'name': student.user.get_full_name(),
            'school': student.school.name,
            'total_score': rating.total_score,
            'level': rating.level,
        })

    return Response({
        "status": "success",
        "level": level,
        "top_students": data
    })





@api_view(['GET'])
def school_ranking(request, level):
    """
    Maktablar reytingini hisoblash va ko‘rsatish (o‘quvchi soni, umumiy ball)
    """
    if level not in ['district', 'region', 'nation']:
        return Response({"status": "error", "message": "Noto'g'ri daraja!"}, status=400)

    # Maktablarning umumiy ballini hisoblash
    rankings = Rating.objects.filter(level=level).values('school').annotate(total_score=Sum('total_score')).order_by('-total_score')

    data = []
    for rank in rankings:
        school = School.objects.get(id=rank['school'])
        data.append({
            'school_name': school.name,
            'total_score': rank['total_score'],
            'level': level,
        })

    return Response({
        "status": "success",
        "level": level,
        "school_rankings": data
    })



@api_view(['GET'])
def district_ranking(request):
    """
    Tuman reytingini hisoblash va ko‘rsatish (o‘quvchilar va maktablar bo‘yicha)
    """
    # Tuman reytingini olish
    rankings = Rating.objects.filter(level='district').values('school').annotate(
        total_score=Sum('total_score')
    ).order_by('-total_score')

    data = []
    for rank in rankings:
        school = School.objects.get(id=rank['school'])
        data.append({
            'school_name': school.name,
            'total_score': rank['total_score'],
            'district': school.district,
        })

    return Response({
        "status": "success",
        "district_ranking": data
    })



@api_view(['GET'])
def region_ranking(request):
    """
    Viloyat reytingini hisoblash va ko‘rsatish (o‘quvchilar va maktablar bo‘yicha)
    """
    # Viloyat reytingini olish
    rankings = Rating.objects.filter(level='region').values('school').annotate(
        total_score=Sum('total_score')
    ).order_by('-total_score')

    data = []
    for rank in rankings:
        school = School.objects.get(id=rank['school'])
        data.append({
            'school_name': school.name,
            'total_score': rank['total_score'],
            'region': school.region,
        })

    return Response({
        "status": "success",
        "region_ranking": data
    })



@api_view(['GET'])
def nation_ranking(request):
    """
    Respublika reytingini hisoblash va ko‘rsatish (o‘quvchilar va maktablar bo‘yicha)
    """
    # Respublika reytingini olish
    rankings = Rating.objects.filter(level='nation').values('school').annotate(
        total_score=Sum('total_score')
    ).order_by('-total_score')

    data = []
    for rank in rankings:
        school = School.objects.get(id=rank['school'])
        data.append({
            'school_name': school.name,
            'total_score': rank['total_score'],
            'nation': school.region,  # Respublika darajasida regiondan foydalanish
        })

    return Response({
        "status": "success",
        "nation_ranking": data
    })
