from quiz.models import QuizSession, SessionQuestion, Question
qs = list(QuizSession.objects.order_by('-id')[:5])
print('SESSIONS:', [(s.id,s.session_type,s.status,s.current_question_index) for s in qs])
if qs:
    s = qs[0]
    print('SESSION_ID', s.id)
    sqs = list(SessionQuestion.objects.filter(session=s).order_by('order'))
    print('SESSIONQUESTIONS:', [(sq.order, sq.question.id, sq.question.question_text[:60]) for sq in sqs])
    print('TOTAL QUESTIONS:', len(sqs))
else:
    print('No sessions found')
