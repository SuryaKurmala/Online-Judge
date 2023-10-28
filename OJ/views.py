from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required

from User.models import User, Submission
from OJ.models import Problem, TestCase
from OJ.forms import CodeForm
from datetime import datetime
from time import time

import os
import subprocess
import os.path
import docker


@login_required(login_url='login')
def problemPage(request):
    problems = Problem.objects.all()
    submissions = Submission.objects.filter(user=request.user, verdict="Accepted")
    accepted_problems = []
    for submission in submissions:
        accepted_problems.append(submission.problem_id)
    context = {'problems': problems, 'accepted_problems': accepted_problems}
    return render(request, 'OJ/problem.html', context)


@login_required(login_url='login')
def descriptionPage(request, problem_id):
    user_id = request.user.id
    problem = get_object_or_404(Problem, id=problem_id)
    user = User.objects.get(id=user_id)
    form = CodeForm()
    context = {'problem': problem, 'user': user, 'user_id': user_id, 'code_form': form}
    return render(request, 'OJ/description.html', context)


@login_required(login_url='login')
def verdictPage(request, problem_id):
     if request.method == 'POST':
        problem = Problem.objects.get(id = problem_id)
        testcase = TestCase.objects.get(problem_id = problem_id)
        verdict, run_time  = "Wrong Answer", 0

        language = request.POST.get('language', '')
        user_code = request.POST.get('user_code', '')
        user_code = user_code.replace('\r\n', '\n').strip()
        print(f"Language: {language}")
        print(f"User Code: {user_code}")
        submission = Submission(user=request.user, problem=problem, submission_time=datetime.now(), 
                                    language=language, user_code=user_code)
        submission.save()
        filename = str(submission.id)

        testcase.output = testcase.output.replace('\r\n','\n').strip() 

        if language == "C++":
            extension = ".cpp"
            cont_name = "oj-cpp"
            compile = f"g++ -o {filename} {filename}.cpp"
            clean = f"{filename} {filename}.cpp"
            docker_img = "gcc"
            exe = f"./{filename}"
            
        elif language == "C":
            extension = ".c"
            cont_name = "oj-c"
            compile = f"gcc -o {filename} {filename}.c"
            clean = f"{filename} {filename}.c"
            docker_img = "gcc"
            exe = f"./{filename}"

        elif language == "Python":
            extension = ".py"
            cont_name = "oj-py3"
            compile = "python3"
            clean = f"{filename}.py"
            docker_img = "python"
            exe = f"python {filename}.py"
        
        elif language == "Java":
            filename = "Main"
            extension = ".java"
            cont_name = "oj-java"
            compile = f"javac {filename}.java"
            clean = f"{filename}.java {filename}.class"
            docker_img = "openjdk"
            exe = f"java {filename}"
        
        file = filename + extension
        filepath = os.path.join(settings.FILES_DIR, file)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as code:
            code.write(user_code)
        print("Local File Path: ", filepath)
        
        try:
            docker_client = docker.from_env()
            container = docker_client.containers.get(cont_name)
            container_state = container.attrs['State']
            if not container_state['Status'] == "running":
                subprocess.run(f"docker start {cont_name}",shell=True)

        except docker.errors.NotFound:
            subprocess.run(f"docker run -dt --name {cont_name} {docker_img}",shell=True)
        subprocess.run(f"docker cp {filepath} {cont_name}:/{file}",shell=True)
        cmp = subprocess.run(f"docker exec {cont_name} {compile}", capture_output=True, shell=True)
        print(cmp)
        if cmp.returncode != 0:
            verdict = "Compilation Error"
            subprocess.run(f"docker exec {cont_name} rm {file}",shell=True)

        else:
            start = time()
            try:
                res = subprocess.run(f'''docker exec {cont_name} sh -c "echo '{testcase.input}' | {exe}"''',
                                                capture_output=True, timeout=1, shell=False)
                run_time = time()-start
                subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)
                print(res)
            except subprocess.TimeoutExpired:
                run_time = time()-start
                verdict = "Time Limit Exceeded"
                subprocess.run(f"docker container kill {cont_name}", shell=True)
                subprocess.run(f"docker start {cont_name}",shell=True)
                subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)

            if verdict != "Time Limit Exceeded" and res.returncode != 0:
                verdict = "Runtime Error"
                

        user_stderr = ""
        user_stdout = ""
        if verdict == "Compilation Error":
            user_stderr = cmp.stderr.decode('utf-8')
        
        elif verdict == "Wrong Answer":
            user_stdout = res.stdout.decode('utf-8')
            if user_stdout == testcase.output:
                verdict = "Accepted"
            if user_stdout == testcase.output + '\n':
                verdict = "Accepted"

<<<<<<< HEAD
=======

        user = User.objects.get(username=request.user)
        previous_verdict = Submission.objects.filter(user=user.id, problem=problem, verdict="Accepted")
        

>>>>>>> 25ebc865f0099788f043d2cb9a90cc0784a5a68a
        submission.verdict = verdict
        submission.user_stdout = user_stdout
        submission.user_stderr = user_stderr
        submission.run_time = run_time
        submission.save()
        os.remove(filepath)

        context = {
            'verdict': verdict,
            'verdict_css_class': 'accepted' if verdict == 'Accepted' else 'wrong-answer' if verdict == 'Wrong Answer' else 'other'
        }
        return render(request,'OJ/verdict.html',context)