from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.db.models import Avg, Count
from .models import Profile, Category, Quiz, Question, QuizAttempt, UserAnswer
from django.http import JsonResponse
import random
import json
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

class RegisterForm(forms.Form):
    first_name = forms.CharField(label="Full Name")
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    role = forms.ChoiceField(choices=Profile.USER_ROLES, label="I am a")
    class_section = forms.CharField(label="Class/Section", required=False)
    department = forms.CharField(label="Department", required=False)

def initialize_categories():
    """Create default categories if none exist."""
    default_categories = [
        {'name': 'Math', 'icon': '➕', 'description': 'Mathematics quizzes'},
        {'name': 'Science', 'icon': '🔬', 'description': 'Science quizzes'},
        {'name': 'History', 'icon': '📜', 'description': 'History quizzes'},
        {'name': 'English', 'icon': '📜', 'description': 'English quizzes'},
        {'name': 'Nepali', 'icon': '📜', 'description': 'Nepali quizzes'},
    ]
    for category in default_categories:
        if not Category.objects.filter(name=category['name']).exists():
            Category.objects.create(**category)

def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid credentials")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] != form.cleaned_data['confirm_password']:
                messages.error(request, "Passwords do not match")
            else:
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name']
                )
                profile = Profile.objects.create(
                    user=user,
                    role=form.cleaned_data['role'],
                    class_section=form.cleaned_data['class_section'] if form.cleaned_data['role'] == 'student' else '',
                    department=form.cleaned_data['department'] if form.cleaned_data['role'] == 'teacher' else ''
                )
                login(request, user)
                return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    if request.user.profile.role == 'student':
        attempts = QuizAttempt.objects.filter(user=request.user)
        quizzes_completed = attempts.count()
        avg_score = attempts.aggregate(Avg('score'))['score__avg'] or 0
        total_students = Profile.objects.filter(role='student').count()
        class_rank = QuizAttempt.objects.filter(score__gt=avg_score).count() + 1 if avg_score else 1
        weakest_subject = Category.objects.filter(quiz__quizattempt__user=request.user).annotate(
            avg_score=Avg('quiz__quizattempt__score')
        ).order_by('avg_score').first()
        
        stats = {
            'quizzes_completed': quizzes_completed,
            'average_score': round(avg_score, 2),
            'quiz_progress': min(quizzes_completed * 10, 100),
            'class_rank': class_rank,
            'rank_progress': min(100 - (class_rank / total_students * 100), 100) if total_students else 100,
            'weakest_subject': weakest_subject.name if weakest_subject else 'N/A',
            'weakest_score': weakest_subject.avg_score if weakest_subject else 0
        }
        recent_attempts = attempts.order_by('-completed_at')[:3]
        top_performers = QuizAttempt.objects.values('user').annotate(score=Avg('score')).order_by('-score')[:3]
        for performer in top_performers:
            performer['user'] = User.objects.get(id=performer['user'])
            performer['score'] = round(performer['score'], 2)
        focus_areas = Category.objects.filter(quiz__quizattempt__user=request.user).annotate(
            score=Avg('quiz__quizattempt__score')
        ).order_by('score')[:2]
        return render(request, 'student_dashboard.html', {
            'stats': stats,
            'recent_attempts': recent_attempts,
            'top_performers': top_performers,
            'focus_areas': focus_areas
        })
    else:
        stats = {
            'total_students': Profile.objects.filter(role='student').count(),
            'avg_class_score': QuizAttempt.objects.aggregate(Avg('score'))['score__avg'] or 0,
            'quizzes_created': Quiz.objects.filter(created_by=request.user).count(),
            'weakest_subject': Category.objects.filter(quiz__quizattempt__score__gt=0).annotate(
                avg_score=Avg('quiz__quizattempt__score')
            ).order_by('avg_score').first().name if Category.objects.filter(quiz__quizattempt__score__gt=0).exists() else 'N/A'
        }
        student_progress = QuizAttempt.objects.values('user', 'quiz__title').annotate(
            score=Avg('score')
        ).order_by('-score')[:3]
        for progress in student_progress:
            progress['student'] = User.objects.get(id=progress['user'])
            progress['quiz_title'] = progress.pop('quiz__title')
            progress['score'] = round(progress['score'], 2)
        recent_quizzes = QuizAttempt.objects.values('quiz').annotate(
            avg_score=Avg('score')
        ).order_by('-quiz__created_at')[:3]
        for result in recent_quizzes:
            result['quiz'] = Quiz.objects.get(id=result['quiz'])
            result['avg_score'] = round(result['avg_score'], 2)
        categories = Category.objects.all()
        return render(request, 'teacher_dashboard.html', {
            'stats': stats,
            'student_progress': student_progress,
            'recent_quizzes': recent_quizzes,
            'categories': categories
        })

@login_required
def create_quiz(request):
    if request.user.profile.role != 'teacher':
        messages.error(request, "Only teachers can create quizzes.")
        return redirect('dashboard')
    
    # Initialize default categories if none exist
    initialize_categories()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        questions_text = request.POST.get('questions')
        
        if not title or not category_id or not questions_text:
            messages.error(request, "All fields are required.")
            return redirect('dashboard')
        
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
            return redirect('dashboard')
        
        quiz = Quiz.objects.create(title=title, category=category, created_by=request.user)
        for line in questions_text.strip().split('\n'):
            parts = line.split('|')
            if len(parts) == 6:
                Question.objects.create(
                    quiz=quiz,
                    text=parts[0].strip(),
                    option1=parts[1].strip(),
                    option2=parts[2].strip(),
                    option3=parts[3].strip(),
                    option4=parts[4].strip(),
                    correct_answer=parts[5].strip()
                )
            else:
                messages.warning(request, f"Invalid question format: {line}. Skipping.")
        messages.success(request, "Quiz created successfully!")
        return redirect('dashboard')
    
    categories = Category.objects.all()
    if not categories:
        messages.error(request, "No categories available. Please create a category first.")
        return redirect('dashboard')
    return render(request, 'create_quiz.html', {'categories': categories})

@login_required
def quiz_list(request):
    if request.user.profile.role != 'student':
        return redirect('dashboard')
    # Ensure categories exist for quiz listing
    initialize_categories()
    categories = Category.objects.all()
    return render(request, 'quiz_list.html', {'categories': categories})

@login_required
def quiz_list_category(request, category_id):
    if request.user.profile.role != 'student':
        return redirect('dashboard')
    category = get_object_or_404(Category, id=category_id)
    quizzes = Quiz.objects.filter(category=category)
    return render(request, 'quiz_list_category.html', {'category': category, 'quizzes': quizzes})


@login_required
def start_quiz(request, quiz_id):
    if request.user.profile.role != 'student':
        return redirect('dashboard')
        
    quiz = get_object_or_404(Quiz, id=quiz_id)
    session_key = f'quiz_{quiz_id}_{request.user.id}'

    # Load questions from session if already saved
    session_data = request.session.get(session_key, {})
    if not session_data.get('questions'):
        # Select and save random questions to session
        questions = list(quiz.questions.all())
        random.shuffle(questions)
        selected_questions = questions[:30]  # you can adjust number
        question_ids = [q.id for q in selected_questions]
        request.session[session_key] = {
            'questions': question_ids,
            'current_index': 0,
            'answers': {}
        }
        request.session.modified = True
    else:
        question_ids = session_data['questions']
        selected_questions = list(quiz.questions.filter(id__in=question_ids))
        # Maintain original order
        selected_questions.sort(key=lambda q: question_ids.index(q.id))

    if request.method == 'POST':
        action = request.POST.get('action')
        current_index = int(request.session[session_key]['current_index'])
        answers = request.session[session_key]['answers']
        selected_answer = request.POST.get('answer')

        if selected_answer:
            answers[str(current_index)] = selected_answer

        if action == 'previous' and current_index > 0:
            current_index -= 1
        elif action == 'next':
            if current_index < len(selected_questions) - 1:
                current_index += 1
            else:
                # Submit quiz
                attempt = QuizAttempt.objects.create(
                    user=request.user,
                    quiz=quiz,
                    total_questions=len(selected_questions)
                )
                score = 0
                for idx, question in enumerate(selected_questions):
                    user_answer = answers.get(str(idx))
                    is_correct = user_answer == question.correct_answer
                    if is_correct:
                        score += 1
                    UserAnswer.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_answer=user_answer or '',
                        is_correct=is_correct
                    )
                attempt.score = score
                attempt.save()
                request.session.pop(session_key, None)
                return redirect('quiz_results', attempt_id=attempt.id)

        # Update session
        request.session[session_key]['current_index'] = current_index
        request.session[session_key]['answers'] = answers
        request.session.modified = True

    current_index = request.session[session_key]['current_index']
    user_answer = request.session[session_key]['answers'].get(str(current_index), '')
    bookmarked_questions = request.session.get('bookmarked_questions', [])

    return render(request, 'quiz.html', {
        'quiz': quiz,
        'questions': selected_questions,
        'current_question': selected_questions[current_index],
        'current_question_index': current_index,
        'user_answer': user_answer,
        'bookmarked_questions': bookmarked_questions,
        'progress': ((current_index + 1) / len(selected_questions)) * 100
    })

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    score_percentage = round((attempt.score / attempt.total_questions) * 100, 2)
    user_answers = UserAnswer.objects.filter(attempt=attempt)

    return render(request, 'quiz_results.html', {
        'attempt': attempt,
        'score_percentage': score_percentage,
        'user_answers': user_answers
    })

@login_required
def bookmark_question(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question_id = data.get('question_id')
        bookmarked = request.session.get('bookmarked_questions', [])
        if question_id in bookmarked:
            bookmarked.remove(question_id)
        else:
            bookmarked.append(question_id)
        request.session['bookmarked_questions'] = bookmarked
        request.session.modified = True
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def bookmarked_questions(request):
    if request.user.profile.role != 'student':
        messages.error(request, "Only students can view bookmarked questions.")
        return redirect('dashboard')
    bookmarked_ids = request.session.get('bookmarked_questions', [])
    questions = Question.objects.filter(id__in=bookmarked_ids)
    return render(request, 'bookmarked_questions.html', {'questions': questions})

@login_required
def create_category(request):
    if request.user.profile.role != 'teacher':
        messages.error(request, "Only teachers can create categories.")
        return redirect('dashboard')
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', '📚')
        description = request.POST.get('description')
        if name and description:
            Category.objects.create(name=name, icon=icon, description=description)
            messages.success(request, "Category created successfully!")
            return redirect('dashboard')
        messages.error(request, "Name and description are required.")
    return render(request, 'create_category.html')

