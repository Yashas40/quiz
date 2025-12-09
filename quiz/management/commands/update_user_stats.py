from django.core.management.base import BaseCommand
from quiz.models import CustomUser, PlayerScore
from django.db.models import Sum, Count, Avg

class Command(BaseCommand):
    help = 'Recalculates and updates user statistics (total_score, games_played, win_rate) based on PlayerScore history.'

    def handle(self, *args, **options):
        self.stdout.write('Starting user stats update...')
        
        users = CustomUser.objects.all()
        count = 0
        
        for user in users:
            # Get all scores for this user
            scores = PlayerScore.objects.filter(player=user)
            
            if not scores.exists():
                user.total_score = 0
                user.games_played = 0
                user.win_rate = 0.0
                user.save()
                continue
                
            # Calculate stats
            stats = scores.aggregate(
                total_score=Sum('score'),
                games_played=Count('id')
            )
            
            total_score = stats['total_score'] or 0
            games_played = stats['games_played'] or 0
            
            # Calculate win rate (accuracy >= 50% counts as a "win" for single player logic consistency)
            # Note: In views.py submit_answer, is_win = score.accuracy >= 50
            wins = 0
            for s in scores:
                if s.accuracy >= 50:
                    wins += 1
            
            win_rate = (wins / games_played * 100) if games_played > 0 else 0.0
            
            # Update user
            user.total_score = total_score
            user.games_played = games_played
            user.win_rate = win_rate
            user.save()
            
            self.stdout.write(f'Updated {user.username}: Score={total_score}, Games={games_played}, WinRate={win_rate:.1f}%')
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully updated stats for {count} users.'))
