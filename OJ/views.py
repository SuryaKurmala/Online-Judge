from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

from User.models import User, Submission
from OJ.models import Problem, TestCase
from OJ.forms import CodeForm
from datetime import datetime
from time import time

import os
import signal
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
        # setting docker-client
        docker_client = docker.from_env()
        Running = "running"

        problem = Problem.objects.get(id=problem_id)
        testcase = TestCase.objects.get(problem_id=problem_id)
        testcase.output = testcase.output.replace('\r\n','\n').strip() 

        verdict = "Wrong Answer" 
        res = ""
        run_time = 0

        form = CodeForm(request.POST)
        user_code = ''
        if form.is_valid():
            user_code = form.cleaned_data.get('user_code')
            user_code = user_code.replace('\r\n','\n').strip()
            
        language = request.POST['language']
        submission = Submission(user=request.user, problem=problem, submission_time=datetime.now(), 
                                    language=language, user_code=user_code)
        submission.save()

        filename = str(submission.id)

        if language == "C++":
            extension = ".cpp"
            cont_name = "oj-cpp"
            compile = f"g++ -o {filename} {filename}.cpp"
            clean = f"{filename} {filename}.cpp"
            docker_img = "gcc:11.2.0"
            exe = f"./{filename}"
            
        elif language == "C":
            extension = ".c"
            cont_name = "oj-c"
            compile = f"gcc -o {filename} {filename}.c"
            clean = f"{filename} {filename}.c"
            docker_img = "gcc:11.2.0"
            exe = f"./{filename}"

        elif language == "Python3":
            extension = ".py"
            cont_name = "oj-py3"
            compile = "python3"
            clean = f"{filename}.py"
            docker_img = "python"
            exe = f"python {filename}.py"
        
        elif language == "Python2":
            extension = ".py"
            cont_name = "oj-py2"
            compile = "python2"
            clean = f"{filename}.py"
            docker_img = "python2"
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
        print(filepath, user_code)
        try:
            code = open(filepath, "w")
            code.write(user_code)
            code.close()
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
        try:
            container = docker_client.containers.get(cont_name)
            container_state = container.attrs['State']
            container_is_running = (container_state['Status'] == Running)
            if not container_is_running:
                subprocess.run(f"docker start {cont_name}",shell=True)
                print(container_state['Status'])
        except docker.errors.NotFound:
            subprocess.run(f"docker run -dt --name {cont_name} {docker_img}",shell=True)


        print(filepath, cont_name, file)


        host_source_path = filepath
        container_dest_path = f"/{file}"

        try:
            docker_cp_command = f"docker cp {host_source_path} {cont_name}:{container_dest_path}"
            subprocess.run(docker_cp_command, shell=True, check=True)
            print("File copied successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        

        cmp = subprocess.run(f"docker exec {cont_name} {compile}", capture_output=True, shell=True)
        if cmp.returncode != 0:
            verdict = "Compilation Error"
            subprocess.run(f"docker exec {cont_name} rm {file}",shell=True)

        else:
            start = time()
            try:
                res = subprocess.run(f"docker exec {cont_name} sh -c 'echo \"{testcase.input}\" | {exe}'",
                                                capture_output=True, timeout=problem.time_limit, shell=True)
                run_time = time()-start
                subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)
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
            if str(user_stdout)==str(testcase.output):
                verdict = "Accepted"
            testcase.output += '\n'
            if str(user_stdout)==str(testcase.output):
                verdict = "Accepted"


        user = User.objects.get(username=request.user)
        previous_verdict = Submission.objects.filter(user=user.id, problem=problem, verdict="Accepted")
        

        submission.verdict = verdict
        submission.user_stdout = user_stdout
        submission.user_stderr = user_stderr
        submission.run_time = run_time
        submission.save()
        print(verdict)
        os.remove(filepath)
        context={'verdict':verdict}
        return render(request,'OJ/verdict.html',context)
