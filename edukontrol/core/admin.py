from django.contrib import admin
from .models import School, Student, Test, Question, Answer, Score, Rating

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'district')
    search_fields = ('name', 'region', 'district')
    list_filter = ('region', 'district')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'grade')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('grade', 'school__region', 'school__district')
    autocomplete_fields = ['school', 'user']

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('subject', 'grade', 'test_type', 'year', 'week', 'month', 'quarter')
    search_fields = ('subject',)
    list_filter = ('test_type', 'grade', 'year')
    ordering = ('-created_at',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'test')
    search_fields = ('text',)
    list_filter = ('test__subject', 'test__test_type')
    
    def short_text(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text',)

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'raw_score', 'weighted_score', 'submitted_at')
    search_fields = ('student__user__username', 'test__subject')
    list_filter = ('test__test_type', 'test__year')
    readonly_fields = ('submitted_at',)

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'school', 'total_score', 'year', 'quarter', 'month', 'level')
    list_filter = ('year', 'level', 'quarter', 'month')
    search_fields = ('student__user__username', 'school__name')
