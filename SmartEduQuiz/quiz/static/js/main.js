document.addEventListener('DOMContentLoaded', function() {
    // Quiz Page: Answer Selection and Timer
    const quizContainer = document.getElementById('quizContainer');
    if (quizContainer) {
        const bookmarkBtn = document.getElementById('bookmarkBtn');
        if (bookmarkBtn) {
            bookmarkBtn.addEventListener('click', function() {
                this.classList.toggle('active');
                fetch('/bookmark/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
                    },
                    body: JSON.stringify({ question_id: this.dataset.questionId })
                });
            });
        }
    }

    // Index Page: Sample Quiz Timer and Answer Selection
    const quizTimer = document.getElementById('quiz-timer');
    if (quizTimer) {
        let timeLeft = 90;
        const timer = setInterval(() => {
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            quizTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            if (timeLeft <= 0) {
                clearInterval(timer);
                quizTimer.textContent = "Time's up!";
            }
        }, 1000);

        const options = document.querySelectorAll('.answer-option');
        options.forEach(option => {
            option.addEventListener('click', function() {
                options.forEach(opt => opt.classList.remove('active', 'correct', 'incorrect'));
                this.classList.add('active');
                const isCorrect = this.getAttribute('data-correct') === 'true';
                if (isCorrect) {
                    this.classList.add('correct');
                } else {
                    this.classList.add('incorrect');
                }
                document.getElementById('explanation').classList.remove('d-none');
            });
        });
    }

    // Student Dashboard: Stat Card Animation
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length) {
        statCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // Teacher Dashboard: Tab Navigation
    const tabs = document.querySelectorAll('.tab');
    if (tabs.length) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
});