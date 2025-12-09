from django.core.management.base import BaseCommand
from quiz.models import CodingProblem
import json

class Command(BaseCommand):
    help = 'Seeds the database with coding problems'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding coding problems...')
        
        # Clear existing problems to avoid duplicates
        CodingProblem.objects.all().delete()
        
        problems = [
            # EASY (10 Questions)
            {
                "title": "Print Hello World",
                "difficulty": "easy",
                "description": "Print the text Hello World.",
                "input_format": "No input",
                "output_format": "Hello World",
                "test_cases": [
                    {"input": "", "expected_output": "Hello World\n"}
                ]
            },
            {
                "title": "Add Two Numbers",
                "difficulty": "easy",
                "description": "Read two integers and print their sum.",
                "input_format": "Two integers a and b",
                "output_format": "Single integer a + b",
                "test_cases": [
                    {"input": "2 3\n", "expected_output": "5\n"},
                    {"input": "-1 4\n", "expected_output": "3\n"},
                    {"input": "0 0\n", "expected_output": "0\n"},
                    {"input": "100 -25\n", "expected_output": "75\n"}
                ]
            },
            {
                "title": "Maximum of Two Numbers",
                "difficulty": "easy",
                "description": "Given two integers a and b, print the larger of the two.",
                "input_format": "Two integers a and b",
                "output_format": "Larger of the two",
                "test_cases": [
                    {"input": "10 20\n", "expected_output": "20\n"},
                    {"input": "5 5\n", "expected_output": "5\n"},
                    {"input": "-1 3\n", "expected_output": "3\n"},
                    {"input": "-10 -2\n", "expected_output": "-2\n"}
                ]
            },
            {
                "title": "Check Even or Odd",
                "difficulty": "easy",
                "description": "Check if an integer n is Even or Odd.",
                "input_format": "Integer n",
                "output_format": "\"Even\" or \"Odd\"",
                "test_cases": [
                    {"input": "7\n", "expected_output": "Odd\n"},
                    {"input": "10\n", "expected_output": "Even\n"},
                    {"input": "0\n", "expected_output": "Even\n"},
                    {"input": "-3\n", "expected_output": "Odd\n"}
                ]
            },
            {
                "title": "Factorial of a Number",
                "difficulty": "easy",
                "description": "Calculate the factorial of a non-negative integer n.",
                "input_format": "Integer n (assume n >= 0)",
                "output_format": "n! (factorial)",
                "test_cases": [
                    {"input": "0\n", "expected_output": "1\n"},
                    {"input": "1\n", "expected_output": "1\n"},
                    {"input": "5\n", "expected_output": "120\n"},
                    {"input": "7\n", "expected_output": "5040\n"}
                ]
            },
            {
                "title": "Reverse a String",
                "difficulty": "easy",
                "description": "Reverse the given string.",
                "input_format": "A string s",
                "output_format": "Reversed string",
                "test_cases": [
                    {"input": "hello\n", "expected_output": "olleh\n"},
                    {"input": "abc\n", "expected_output": "cba\n"},
                    {"input": "a\n", "expected_output": "a\n"},
                    {"input": "racecar\n", "expected_output": "racecar\n"}
                ]
            },
            {
                "title": "Sum of Digits",
                "difficulty": "easy",
                "description": "Calculate the sum of digits of a non-negative integer n.",
                "input_format": "Integer n (non-negative)",
                "output_format": "Sum of its digits",
                "test_cases": [
                    {"input": "1234\n", "expected_output": "10\n"},
                    {"input": "0\n", "expected_output": "0\n"},
                    {"input": "9\n", "expected_output": "9\n"},
                    {"input": "1005\n", "expected_output": "6\n"}
                ]
            },
            {
                "title": "Multiplication Table",
                "difficulty": "easy",
                "description": "Print the multiplication table of n from 1 to 10.",
                "input_format": "Integer n",
                "output_format": "10 numbers: n*1 n*2 ... n*10 (space-separated)",
                "test_cases": [
                    {"input": "3\n", "expected_output": "3 6 9 12 15 18 21 24 27 30\n"},
                    {"input": "5\n", "expected_output": "5 10 15 20 25 30 35 40 45 50\n"},
                    {"input": "1\n", "expected_output": "1 2 3 4 5 6 7 8 9 10\n"},
                    {"input": "10\n", "expected_output": "10 20 30 40 50 60 70 80 90 100\n"}
                ]
            },
            {
                "title": "Count Vowels in a String",
                "difficulty": "easy",
                "description": "Count the number of vowels (a, e, i, o, u case-insensitive) in a string.",
                "input_format": "String s",
                "output_format": "Integer = number of vowels",
                "test_cases": [
                    {"input": "apple\n", "expected_output": "2\n"},
                    {"input": "BANANA\n", "expected_output": "3\n"},
                    {"input": "sky\n", "expected_output": "0\n"},
                    {"input": "Education\n", "expected_output": "5\n"}
                ]
            },
            {
                "title": "Check Leap Year",
                "difficulty": "easy",
                "description": "Check if a year is a leap year. (Leap if divisible by 400, or divisible by 4 but not by 100)",
                "input_format": "Integer year",
                "output_format": "\"Leap Year\" or \"Not Leap Year\"",
                "test_cases": [
                    {"input": "2024\n", "expected_output": "Leap Year\n"},
                    {"input": "2023\n", "expected_output": "Not Leap Year\n"},
                    {"input": "2000\n", "expected_output": "Leap Year\n"},
                    {"input": "1900\n", "expected_output": "Not Leap Year\n"}
                ]
            },

            # MEDIUM (10 Questions)
            {
                "title": "Palindrome Check",
                "difficulty": "medium",
                "description": "Check if a string is a palindrome.",
                "input_format": "String s",
                "output_format": "\"Yes\" if palindrome, otherwise \"No\"",
                "test_cases": [
                    {"input": "madam\n", "expected_output": "Yes\n"},
                    {"input": "racecar\n", "expected_output": "Yes\n"},
                    {"input": "hello\n", "expected_output": "No\n"},
                    {"input": "a\n", "expected_output": "Yes\n"}
                ]
            },
            {
                "title": "Fibonacci Series",
                "difficulty": "medium",
                "description": "Print the first n Fibonacci numbers (starting 0 1 ...).",
                "input_format": "Integer n (number of terms)",
                "output_format": "First n Fibonacci numbers (space-separated)",
                "test_cases": [
                    {"input": "1\n", "expected_output": "0\n"},
                    {"input": "2\n", "expected_output": "0 1\n"},
                    {"input": "6\n", "expected_output": "0 1 1 2 3 5\n"},
                    {"input": "8\n", "expected_output": "0 1 1 2 3 5 8 13\n"}
                ]
            },
            {
                "title": "Armstrong Number",
                "difficulty": "medium",
                "description": "Check if a 3-digit number is an Armstrong number (sum of cubes of its digits = number).",
                "input_format": "Integer n (3-digit)",
                "output_format": "\"Armstrong Number\" or \"Not Armstrong Number\"",
                "test_cases": [
                    {"input": "153\n", "expected_output": "Armstrong Number\n"},
                    {"input": "370\n", "expected_output": "Armstrong Number\n"},
                    {"input": "123\n", "expected_output": "Not Armstrong Number\n"},
                    {"input": "407\n", "expected_output": "Armstrong Number\n"}
                ]
            },
            {
                "title": "GCD of Two Numbers",
                "difficulty": "medium",
                "description": "Find the Greatest Common Divisor (GCD) of two numbers.",
                "input_format": "Two integers a, b",
                "output_format": "gcd(a, b)",
                "test_cases": [
                    {"input": "24 36\n", "expected_output": "12\n"},
                    {"input": "10 15\n", "expected_output": "5\n"},
                    {"input": "7 13\n", "expected_output": "1\n"},
                    {"input": "100 25\n", "expected_output": "25\n"}
                ]
            },
            {
                "title": "Remove Duplicates from List",
                "difficulty": "medium",
                "description": "Remove duplicates from a list of integers while preserving order.",
                "input_format": "List of integers (space-separated)",
                "output_format": "List without duplicates in the same order (space-separated)",
                "test_cases": [
                    {"input": "1 2 2 3 3 4\n", "expected_output": "1 2 3 4\n"},
                    {"input": "5 5 5\n", "expected_output": "5\n"},
                    {"input": "1 2 3\n", "expected_output": "1 2 3\n"},
                    {"input": "4 4 3 2 2 1\n", "expected_output": "4 3 2 1\n"}
                ]
            },
            {
                "title": "Sort Array Without Built-in Sort",
                "difficulty": "medium",
                "description": "Sort a list of integers in ascending order.",
                "input_format": "List of integers (space-separated)",
                "output_format": "Sorted list (ascending, space-separated)",
                "test_cases": [
                    {"input": "3 1 2\n", "expected_output": "1 2 3\n"},
                    {"input": "5 4 3 2 1\n", "expected_output": "1 2 3 4 5\n"},
                    {"input": "1 1 1\n", "expected_output": "1 1 1\n"},
                    {"input": "-1 0 -5 2\n", "expected_output": "-5 -1 0 2\n"}
                ]
            },
            {
                "title": "Count Words in a Sentence",
                "difficulty": "medium",
                "description": "Count the number of words in a sentence.",
                "input_format": "A string sentence s",
                "output_format": "Number of words",
                "test_cases": [
                    {"input": "I love programming\n", "expected_output": "3\n"},
                    {"input": "Hello\n", "expected_output": "1\n"},
                    {"input": " multiple spaces here \n", "expected_output": "3\n"},
                    {"input": "\n", "expected_output": "0\n"}
                ]
            },
            {
                "title": "Binary to Decimal Conversion",
                "difficulty": "medium",
                "description": "Convert a binary string to a decimal integer.",
                "input_format": "Binary string b",
                "output_format": "Decimal integer",
                "test_cases": [
                    {"input": "1010\n", "expected_output": "10\n"},
                    {"input": "0\n", "expected_output": "0\n"},
                    {"input": "1\n", "expected_output": "1\n"},
                    {"input": "1111\n", "expected_output": "15\n"}
                ]
            },
            {
                "title": "Second Largest Number",
                "difficulty": "medium",
                "description": "Find the second largest number in a list of distinct integers.",
                "input_format": "List of distinct integers (space-separated)",
                "output_format": "Second largest integer",
                "test_cases": [
                    {"input": "4 2 9 7\n", "expected_output": "7\n"},
                    {"input": "1 2 3\n", "expected_output": "2\n"},
                    {"input": "10 5\n", "expected_output": "5\n"},
                    {"input": "-1 -5 -3\n", "expected_output": "-3\n"}
                ]
            },
            {
                "title": "Character Frequency",
                "difficulty": "medium",
                "description": "Count frequency of each character in a string. Output format: char:count sorted alphabetically by char.",
                "input_format": "String s",
                "output_format": "Frequency of each character (e.g. a:2 b:1)",
                "test_cases": [
                    {"input": "banana\n", "expected_output": "a:3 b:1 n:2\n"},
                    {"input": "aabb\n", "expected_output": "a:2 b:2\n"},
                    {"input": "abc\n", "expected_output": "a:1 b:1 c:1\n"},
                    {"input": "\n", "expected_output": "\n"}
                ]
            },

            # HARD (10 Questions)
            {
                "title": "Longest Substring Without Repeating Characters",
                "difficulty": "hard",
                "description": "Find the length of the longest substring with all unique characters.",
                "input_format": "String s",
                "output_format": "Length of the longest substring",
                "test_cases": [
                    {"input": "abcabcbb\n", "expected_output": "3\n"},
                    {"input": "bbbbb\n", "expected_output": "1\n"},
                    {"input": "pwwkew\n", "expected_output": "3\n"},
                    {"input": "\n", "expected_output": "0\n"}
                ]
            },
            {
                "title": "Group Anagrams",
                "difficulty": "hard",
                "description": "Group anagrams together from a list of strings. Output each group on a new line, sorted.",
                "input_format": "List of strings (space-separated)",
                "output_format": "Groups of anagrams",
                "test_cases": [
                    {"input": "eat tea tan ate nat bat\n", "expected_output": "ate eat tea\nbat\nnat tan\n"},
                    {"input": "a\n", "expected_output": "a\n"},
                    {"input": "ab ba abc\n", "expected_output": "ab ba\nabc\n"}
                ]
            },
            {
                "title": "Maximum Subarray Sum",
                "difficulty": "hard",
                "description": "Find the maximum possible sum of a contiguous subarray (Kadane's Algorithm).",
                "input_format": "List of integers (space-separated)",
                "output_format": "Maximum sum",
                "test_cases": [
                    {"input": "-2 1 -3 4 -1 2 1 -5 4\n", "expected_output": "6\n"},
                    {"input": "1\n", "expected_output": "1\n"},
                    {"input": "5 4 -1 7 8\n", "expected_output": "23\n"},
                    {"input": "-1 -2 -3\n", "expected_output": "-1\n"}
                ]
            },
            {
                "title": "N-Queens Solutions",
                "difficulty": "hard",
                "description": "Count the number of ways to place n queens so none attack each other.",
                "input_format": "Integer n",
                "output_format": "Number of ways",
                "test_cases": [
                    {"input": "1\n", "expected_output": "1\n"},
                    {"input": "2\n", "expected_output": "0\n"},
                    {"input": "3\n", "expected_output": "0\n"},
                    {"input": "4\n", "expected_output": "2\n"}
                ]
            },
            {
                "title": "Merge Intervals",
                "difficulty": "hard",
                "description": "Merge overlapping intervals. Input format: start1 end1 start2 end2 ...",
                "input_format": "List of intervals flattened (e.g. 1 3 2 6 for [1,3],[2,6])",
                "output_format": "Merged intervals flattened",
                "test_cases": [
                    {"input": "1 3 2 6 8 10 15 18\n", "expected_output": "1 6 8 10 15 18\n"},
                    {"input": "1 4 4 5\n", "expected_output": "1 5\n"},
                    {"input": "1 2 3 4\n", "expected_output": "1 2 3 4\n"},
                    {"input": "6 8 1 9 2 4 4 7\n", "expected_output": "1 9\n"}
                ]
            },
            {
                "title": "Word Search in Grid",
                "difficulty": "hard",
                "description": "Check if a word exists in a grid (horizontally/vertically). Input: R C, then R lines of grid, then Word.",
                "input_format": "R C, Grid lines, Word",
                "output_format": "True or False",
                "test_cases": [
                    {"input": "3 4\nA B C E\nS F C S\nA D E E\nABCCED\n", "expected_output": "True\n"},
                    {"input": "3 4\nA B C E\nS F C S\nA D E E\nSEE\n", "expected_output": "True\n"},
                    {"input": "3 4\nA B C E\nS F C S\nA D E E\nABCB\n", "expected_output": "False\n"},
                    {"input": "1 1\nA\nA\n", "expected_output": "True\n"}
                ]
            },
            {
                "title": "LRU Cache Simulation",
                "difficulty": "hard",
                "description": "Simulate LRU Cache. Input: Capacity, then operations (PUT k v or GET k). Output: GET results.",
                "input_format": "Capacity, then lines of operations. End with END.",
                "output_format": "GET results space-separated",
                "test_cases": [
                    {"input": "2\nPUT 1 1\nPUT 2 2\nGET 1\nPUT 3 3\nGET 2\nPUT 4 4\nGET 1\nGET 3\nGET 4\nEND\n", "expected_output": "1 -1 -1 3 4\n"},
                    {"input": "1\nPUT 1 10\nGET 1\nPUT 2 20\nGET 1\nGET 2\nEND\n", "expected_output": "10 -1 20\n"}
                ]
            },
            {
                "title": "Shortest Path (Dijkstra)",
                "difficulty": "hard",
                "description": "Find shortest distance from start node 0 to all nodes. Input: N M (nodes, edges), then M lines u v w, then Start.",
                "input_format": "N M, edges, Start",
                "output_format": "Distances to 0, 1, ... N-1 space-separated",
                "test_cases": [
                    {"input": "4 5\n0 1 4\n0 2 1\n2 1 2\n1 3 1\n2 3 5\n0\n", "expected_output": "0 3 1 4\n"},
                    {"input": "3 3\n0 1 1\n1 2 1\n0 2 5\n0\n", "expected_output": "0 1 2\n"}
                ]
            },
            {
                "title": "Count Inversions",
                "difficulty": "hard",
                "description": "Count inversions in an array (i < j and a[i] > a[j]).",
                "input_format": "List of integers",
                "output_format": "Number of inversions",
                "test_cases": [
                    {"input": "2 4 1 3 5\n", "expected_output": "3\n"},
                    {"input": "1 2 3 4 5\n", "expected_output": "0\n"},
                    {"input": "5 4 3 2 1\n", "expected_output": "10\n"},
                    {"input": "1\n", "expected_output": "0\n"}
                ]
            },
            {
                "title": "Solve Sudoku",
                "difficulty": "hard",
                "description": "Solve a 9x9 Sudoku grid (0 for empty). Output the solved grid.",
                "input_format": "9 lines of 9 integers",
                "output_format": "9 lines of 9 integers",
                "test_cases": [
                    {
                        "input": "5 3 0 0 7 0 0 0 0\n6 0 0 1 9 5 0 0 0\n0 9 8 0 0 0 0 6 0\n8 0 0 0 6 0 0 0 3\n4 0 0 8 0 3 0 0 1\n7 0 0 0 2 0 0 0 6\n0 6 0 0 0 0 2 8 0\n0 0 0 4 1 9 0 0 5\n0 0 0 0 8 6 0 7 9\n",
                        "expected_output": "5 3 4 6 7 8 9 1 2\n6 7 2 1 9 5 3 4 8\n1 9 8 3 4 2 5 6 7\n8 5 9 7 6 1 4 2 3\n4 2 6 8 5 3 7 9 1\n7 1 3 9 2 4 8 5 6\n9 6 1 5 3 7 2 8 4\n2 8 7 4 1 9 6 3 5\n3 4 5 2 8 6 1 7 9\n"
                    }
                ]
            }
        ]
        
        for p_data in problems:
            CodingProblem.objects.create(**p_data)
            
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(problems)} coding problems'))
