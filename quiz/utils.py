import requests
import base64
import time
import json
import os
from django.conf import settings

def call_judge0(source_code, language_id, stdin, expected_output):
    """
    Call Judge0 API to execute code.
    
    Args:
        source_code (str): The source code to execute.
        language_id (int): The ID of the language (e.g., 71 for Python, 54 for C++, 63 for JS).
        stdin (str): Input for the program.
        expected_output (str): The expected output to compare against.
        
    Returns:
        dict: Result containing status, stdout, stderr, etc.
    """
    url = "https://judge0-ce.p.rapidapi.com/submissions"
    
    # Encode data
    encoded_source = base64.b64encode(source_code.encode('utf-8')).decode('utf-8')
    encoded_stdin = base64.b64encode(stdin.encode('utf-8')).decode('utf-8')
    encoded_expected = base64.b64encode(expected_output.encode('utf-8')).decode('utf-8')
    
    payload = {
        "language_id": language_id,
        "source_code": encoded_source,
        "stdin": encoded_stdin,
        # "expected_output": encoded_expected  <-- Don't send this, we compare locally
    }
    
    # Get API key from environment or use fallback
    api_key = os.environ.get('RAPIDAPI_JUDGE0_KEY', "d214365c85mshd300b62a7d9c7efp16bc56jsnb5739ff86fc7")
    
    headers = {
        "content-type": "application/json",
        "Content-Type": "application/json",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
    }
    
    try:
        # Step 1: Submit Code
        response = requests.post(url, json=payload, headers=headers, params={"base64_encoded": "true", "fields": "*"})
        response.raise_for_status()
        token = response.json().get("token")
        
        if not token:
            return {'status_id': 13, 'status_description': 'Internal Error', 'stderr': 'No token received from Judge0'}
            
        # Step 2: Poll for results
        for _ in range(10):  # Poll up to 10 times
            time.sleep(1)
            result_url = f"{url}/{token}"
            result_response = requests.get(result_url, headers=headers, params={"base64_encoded": "true", "fields": "*"})
            result_data = result_response.json()
            
            status_id = result_data.get("status", {}).get("id")
            
            if status_id not in [1, 2]:  # 1=In Queue, 2=Processing
                # Decode outputs
                stdout = result_data.get("stdout")
                if stdout:
                    stdout = base64.b64decode(stdout).decode('utf-8').strip()
                else:
                    stdout = ""
                
                stderr = result_data.get("stderr")
                if stderr:
                    stderr = base64.b64decode(stderr).decode('utf-8').strip()
                    
                compile_output = result_data.get("compile_output")
                if compile_output:
                    compile_output = base64.b64decode(compile_output).decode('utf-8').strip()
                    if stderr:
                        stderr += "\n" + compile_output
                    else:
                        stderr = compile_output

                # Local Comparison Logic
                # Only override status if it was "Accepted" (3) or just finished without error
                # Judge0 returns 3 only if we sent expected_output and it matched.
                # Since we didn't send it, Judge0 will likely return 3 (Accepted) if it ran successfully.
                
                if status_id == 3: # Judge0 says it ran successfully
                    if stdout == expected_output.strip():
                        status_id = 3 # Accepted
                        status_desc = "Accepted"
                    else:
                        status_id = 4 # Wrong Answer
                        status_desc = "Wrong Answer"
                else:
                     status_desc = result_data.get("status", {}).get("description")

                return {
                    'status_id': status_id,
                    'status_description': status_desc,
                    'stdout': stdout,
                    'stderr': stderr,
                    'time': result_data.get("time"),
                    'memory': result_data.get("memory")
                }
                
        return {'status_id': 13, 'status_description': 'Internal Error (Timeout)', 'stderr': 'Judge0 timed out'}
        
    except Exception as e:
        return {'status_id': 13, 'status_description': 'Internal Error', 'stderr': str(e)}
