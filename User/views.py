from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from User.models import Submission
from .forms import RegistrationForm

from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from .forms import RegistrationForm, UpdateProfileForm



def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login')
    else:
        form = RegistrationForm()
    context = {'form': form}
    return render(request, 'register.html', context)



def loginPage(request):
    if request.user.is_authenticated:
        return redirect('problems')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('problems')
            else:
                messages.info(request, 'Username/Password is incorrect')

        context = {}
        return render(request, 'login.html', context)


def logoutPage(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def allSubmissionPage(request):
    submissions = Submission.objects.filter(user=request.user.id)
    return render(request, 'submission.html', {'submissions': submissions})

from django.contrib.auth.views import PasswordChangeView

class ChangePasswordView(PasswordChangeView):
    template_name = 'change_password.html'

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error changing your password.')
        return render(self.request, self.template_name, {'form': form})

from django.contrib.auth.views import PasswordChangeDoneView

class PasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'password_change_done.html'

@login_required(login_url='login')
def account(request):
  user = request.user
  context = {
    'user': user,
  }
  return render(request, 'account.html', context)
