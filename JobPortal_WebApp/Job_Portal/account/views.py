from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect , get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login, authenticate
from werkzeug.security import generate_password_hash

from account.forms import *
from jobapp.permission import user_is_employee 
from jobapp.models import FlaskUser
import logging

logger = logging.getLogger('jobapp')

def get_success_url(request):

    """
    Handle Success Url After LogIN

    """
    if request.user.is_superuser:
        return reverse('jobapp:admin-dashboard')
    elif 'next' in request.GET and request.GET['next'] != '':
        return request.GET['next']
    else:
        return reverse('jobapp:home')



def employee_registration(request):

    """
    Handle Employee Registration

    """
    form = EmployeeRegistrationForm(request.POST or None)
    if form.is_valid():
        form = form.save()
        return redirect('account:login')
    context={
        
            'form':form
        }

    return render(request,'account/employee-registration.html',context)


def employer_registration(request):

    """
    Handle Employee Registration 

    """

    form = EmployerRegistrationForm(request.POST or None)
    if form.is_valid():
        form = form.save()
        return redirect('account:login')
    context={
        
            'form':form
        }

    return render(request,'account/employer-registration.html',context)


@login_required(login_url=reverse_lazy('accounts:login'))
@user_is_employee
def employee_edit_profile(request, id=id):

    """
    Handle Employee Profile Update Functionality

    """

    user = get_object_or_404(User, id=id)
    form = EmployeeProfileEditForm(request.POST or None, instance=user)
    if form.is_valid():
        form = form.save()
        messages.success(request, 'Your Profile Was Successfully Updated!')
        return redirect(reverse("account:edit-profile", kwargs={
                                    'id': form.id
                                    }))
    context={
        
            'form':form
        }

    return render(request,'account/employee-edit-profile.html',context)



def user_logIn(request):

    """
    Provides users to logIn

    """

    form = UserLoginForm(request.POST or None)
    

    if request.user.is_authenticated:
        return redirect('/')
    
    else:
        if request.method == 'POST':
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                user = authenticate(request, email=email, password=password)
                
                if user is not None:
                    try:
                        # Try to get existing FlaskUser
                        try:
                            flask_user = FlaskUser.objects.using('flaskdb').get(email=email)
                            flask_user.is_active = True
                            flask_user.save()
                        except FlaskUser.DoesNotExist:
                            # Create FlaskUser if it doesn't exist
                            flask_user = FlaskUser.objects.using('flaskdb').create(
                                username=email,
                                email=email,
                                mobile='',
                                role=user.role,
                                password_hash=generate_password_hash(password)
                            )
                        
                        login(request, user)
                        messages.success(request, 'Logged in successfully!')
                        return HttpResponseRedirect(get_success_url(request))
                    except Exception as e:
                        messages.error(request, f'Error updating user status: {str(e)}')
                        logger.error(f'Error updating Flask user status: {str(e)}')
                else:
                    messages.error(request, 'Invalid email or password')
    context = {
        'form': form,
    }

    return render(request,'account/login.html',context)


def user_logOut(request):
    """
    Provide the ability to logout
    """
    auth.logout(request)
    messages.success(request, 'You are Successfully logged out')
    return redirect('account:login')

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                # Save user directly to Flask database
                user_data = {
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'mobile': form.cleaned_data.get('mobile', ''),
                    'role': form.cleaned_data.get('role', 'employee')
                }
                flask_user = FlaskUser.objects.using('flaskdb').create(**user_data)
                
                # Also save to Django for compatibility
                user = form.save()
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                logger.error(f'Error creating user account: {str(e)}')
    else:
        form = UserRegisterForm()
    return render(request, 'account/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                # Update user in Flask database
                flask_user = FlaskUser.objects.using('flaskdb').get(username=request.user.username)
                flask_user.email = form.cleaned_data['email']
                flask_user.mobile = form.cleaned_data.get('mobile', flask_user.mobile)
                flask_user.save()
                
                # Also update Django user
                form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('account:profile')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
                logger.error(f'Error updating user profile: {str(e)}')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'account/profile.html', {'form': form})