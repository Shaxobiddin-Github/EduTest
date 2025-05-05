from django.db import models

# Create your models here.


class School(models.Model):
    name = models.CharField(max_length=255)
    region = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    def __str__(self):
        return self.name


from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    grade = models.IntegerField()  # sinfi (1-11)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name()



class Test(models.Model):
    TEST_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarter', 'Quarter'),
        ('annual', 'Annual'),
        ('final', 'Final Exam'),
    ]
    subject = models.CharField(max_length=100)
    grade = models.IntegerField()
    test_type = models.CharField(max_length=10, choices=TEST_TYPE_CHOICES)
    week = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(null=True, blank=True)
    quarter = models.PositiveSmallIntegerField(null=True, blank=True)
    year = models.IntegerField(default=2025)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_test_type_display()} - {self.subject} ({self.grade}-grade)"

    


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text[:50]

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text



class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    raw_score = models.FloatField()  # nechta to‘g‘ri javob
    weighted_score = models.FloatField()  # og‘irlikka qarab ball (3x, 6x, 10x)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'test')

    def __str__(self):
        return f"{self.student} - {self.test}"



class Rating(models.Model):
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE)
    school = models.ForeignKey(School, null=True, blank=True, on_delete=models.CASCADE)
    total_score = models.FloatField()
    year = models.IntegerField(default=2025)
    quarter = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(null=True, blank=True)
    level = models.CharField(max_length=20, choices=[  # reyting darajasi
        ('school', 'School'),
        ('district', 'District'),
        ('region', 'Region'),
        ('nation', 'Nation'),
    ])

    def __str__(self):
        return f"{self.level} rating: {self.total_score}"
