from django.db import models
from OJ.models import Problem
from django.contrib.auth.models import User

class Submission(models.Model):
    LANGUAGES = (("C++", "C++"), ("C", "C"), ("Python", "Python"))
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    problem = models.ForeignKey(Problem, null=True, on_delete=models.SET_NULL)
    user_code = models.TextField(max_length=10000, default="")
    user_stdout = models.TextField(max_length=10000, default="")
    user_stderr = models.TextField(max_length=10000, default="")
    submission_time = models.DateTimeField(auto_now_add=True, null=True)
    run_time = models.FloatField(null=True, default=0)
    language = models.CharField(
        max_length=10, choices=LANGUAGES, default="C++")
    verdict = models.CharField(max_length=100, default="Wrong Answer")

    class Meta:
        ordering = ['-submission_time']

    def __str__(self):
        return str(self.submission_time) + " : @" + str(self.user) + " : " + self.problem.name + " : " + self.verdict + " : " + self.language