from quiz.views import generate_mcq_questions
q = generate_mcq_questions(5, [], 'mixed', 15)
print('GEN COUNT', len(q))
for i,qq in enumerate(q):
    print(i, qq.get('payload') if isinstance(qq, dict) else qq)
