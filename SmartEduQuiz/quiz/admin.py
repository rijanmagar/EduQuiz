from django.contrib import admin
from .models import Quiz, Question, UserAnswer, QuizAttempt
from django.contrib.auth import get_user_model
User = get_user_model()

admin.site.register(User)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(UserAnswer)
admin.site.register(QuizAttempt)