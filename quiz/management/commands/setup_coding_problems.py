from django.core.management.base import BaseCommand
from quiz.models import CodingProblem
import json

class Command(BaseCommand):
    help = 'Resets and populates CodingProblem table with Hello World and other questions.'

    def handle(self, *args, **options):
        self.stdout.write('Resetting Coding Problems...')
        
        # 1. Clear existing
        CodingProblem.objects.all().delete()
        
        # 2. Create Hello World (Priority 1)
        CodingProblem.objects.create(
            title="Hello World",
            difficulty="easy",
            description='Write a program that prints "Hello World" to the standard output.',
            input_format='None',
            output_format='The string "Hello World"',
            test_cases=json.dumps([
                {'input': '', 'expected_output': 'Hello World'}
            ]),
            starter_code="def hello_world():\n    # TODO: Print 'Hello World'\n    pass\n\nif __name__ == '__main__':\n    hello_world()"
        )
        
        # 3. Create other problems
        problems = [
            {
                "title": "Add Two Numbers",
                "difficulty": "easy",
                "description": "Write a program that reads two integers from stdin and prints their sum.",
                "input_format": "Two integers separated by space",
                "output_format": "The sum of the two integers",
                "test_cases": json.dumps([
                    {'input': '5 10', 'expected_output': '15'},
                    {'input': '-3 8', 'expected_output': '5'}
                ]),
                "starter_code": "import sys\n\n# Read input from stdin\ninput_str = sys.stdin.read().split()\n# TODO: Calculate and print sum\npass"
            },
            {
                "title": "Reverse String",
                "difficulty": "easy",
                "description": "Write a program that reads a string from stdin and prints it reversed.",
                "input_format": "A single string",
                "output_format": "The reversed string",
                "test_cases": json.dumps([
                    {'input': 'hello', 'expected_output': 'olleh'},
                    {'input': 'python', 'expected_output': 'nohtyp'}
                ]),
                "starter_code": "import sys\n\n# Read input from stdin\ninput_str = sys.stdin.read().strip()\n# TODO: Print reversed string\npass"
            },
            {
                "title": "Is Even",
                "difficulty": "easy",
                "description": "Write a program that checks if a number is even. Print 'True' if even, 'False' otherwise.",
                "input_format": "An integer n",
                "output_format": "'True' or 'False'",
                "test_cases": json.dumps([
                    {'input': '2', 'expected_output': 'True'},
                    {'input': '3', 'expected_output': 'False'}
                ]),
                "starter_code": "import sys\n\n# Read input from stdin\ninput_str = sys.stdin.read().strip()\n# TODO: Print True if even, False otherwise\npass"
            },
             {
                "title": "Factorial",
                "difficulty": "medium",
                "description": "Write a program to calculate the factorial of a number n.",
                "input_format": "An integer n >= 0",
                "output_format": "The factorial of n",
                "test_cases": json.dumps([
                    {'input': '5', 'expected_output': '120'},
                    {'input': '0', 'expected_output': '1'}
                ]),
                "starter_code": "import sys\n\ndef factorial(n):\n    # TODO: Implement factorial\n    return 1\n\ninput_str = sys.stdin.read().strip()\nif input_str:\n    n = int(input_str)\n    print(factorial(n))"
            }
        ]
        
        for p in problems:
            CodingProblem.objects.create(**p)
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(problems) + 1} coding problems.'))
