from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import Http404, HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.serializers import serialize
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.views.decorators.http import require_POST
from django.utils import timezone
import requests
import logging
import json
from datetime import datetime

from account.models import User
from jobapp.forms import *
from jobapp.models import *
from jobapp.permission import *
from jobapp.models import Contact
from .models import Job, Applicant, Contact, JobRating, FlaskContactMessage, FlaskJobApplication, FlaskJob, FlaskUser
User = get_user_model()

logger = logging.getLogger('jobapp')

def save_to_flask(model_type, data):
    """
    Save data directly to Flask database
    """
    try:
        if model_type == 'user':
            # Save user to Flask
            flask_user = FlaskUser.objects.using('flaskdb').create(
                username=data['username'],
                email=data['email'],
                mobile=data.get('mobile', ''),
                role=data.get('role', 'user'),
                password_hash=data.get('password_hash', '')
            )
            logger.info(f'Successfully created user in Flask database: {data["username"]}')
            return flask_user

        elif model_type == 'job':
            # Save job to Flask
            flask_job = FlaskJob.objects.using('flaskdb').create(
                title=data['title'],
                company=data['company'],
                description=data['description'],
                location=data['location'],
                salary=data.get('salary', ''),
                experience=data.get('experience', ''),
                department=data.get('department', ''),
                company_type=data.get('company_type', ''),
                work_mode=data.get('work_mode', ''),
                date_posted=data.get('date_posted', datetime.now().strftime('%Y-%m-%d'))
            )
            logger.info(f'Successfully created job in Flask database: {data["title"]}')
            return flask_job

        elif model_type == 'application':
            # Save application to Flask
            flask_application = FlaskJobApplication.objects.using('flaskdb').create(
                user_id=data['user_id'],
                job_id=data['job_id'],
                status=data.get('status', 'Pending'),
                cover_letter=data.get('cover_letter', ''),
                date_applied=datetime.now()
            )
            logger.info(f'Successfully created application in Flask database for job ID: {data["job_id"]}')
            return flask_application

        elif model_type == 'contact':
            # Save contact message to Flask
            flask_contact = FlaskContactMessage.objects.using('flaskdb').create(
                name=data['name'],
                email=data['email'],
                message=data['message'],
                date_submitted=datetime.now()
            )
            logger.info(f'Successfully created contact message in Flask database from: {data["email"]}')
            return flask_contact

    except Exception as e:
        logger.error(f'Error saving {model_type} to Flask: {str(e)}')
        raise

def sync_user_to_flask(user):
    """
    Sync Django user to Flask database
    """
    try:
        # Check if user already exists in Flask
        flask_user = FlaskUser.objects.using('flaskdb').filter(django_user_id=user.id).first()
        
        if flask_user:
            # Update existing user
            flask_user.username = user.username
            flask_user.email = user.email
            flask_user.first_name = user.first_name
            flask_user.last_name = user.last_name
            flask_user.role = user.role
            flask_user.is_active = user.is_active
            flask_user.save()
            logger.info(f'Updated Flask user with Django user ID {user.id}')
        else:
            # Create new user in Flask
            FlaskUser.objects.using('flaskdb').create(
                django_user_id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_active=user.is_active
            )
            logger.info(f'Created new Flask user for Django user ID {user.id}')
    except Exception as e:
        logger.error(f'Error syncing user to Flask: {str(e)}')
        raise

def sync_to_flask(model_instance, model_type):
    """
    Generic function to sync Django records to Flask database
    """
    try:
        if model_type == 'user':
            sync_user_to_flask(model_instance)
            
        elif model_type == 'job':
            # Sync job to Flask
            FlaskJob.objects.using('flaskdb').create(
                django_job_id=model_instance.id,
                title=model_instance.title,
                description=model_instance.description,
                location=model_instance.location,
                job_type=model_instance.job_type,
                company=model_instance.company_name,
                company_description=model_instance.company_description,
                website=model_instance.website,
                is_published=model_instance.is_published,
                is_closed=model_instance.is_closed
            )
            logger.info(f'Successfully synced new job (ID: {model_instance.id}) to Flask database')
            
        elif model_type == 'application':
            # Sync application to Flask
            FlaskJobApplication.objects.using('flaskdb').create(
                django_application_id=model_instance.id,
                user_id=model_instance.user.id,
                job_id=model_instance.job.id,
                status=model_instance.status,
                resume=model_instance.resume.name if model_instance.resume else None
            )
            logger.info(f'Successfully synced new application (ID: {model_instance.id}) to Flask database')
            
        elif model_type == 'contact':
            # Sync contact message to Flask
            FlaskContactMessage.objects.using('flaskdb').create(
                name=model_instance.name,
                email=model_instance.email,
                message=model_instance.message,
                date_submitted=datetime.now()
            )
            logger.info(f'Successfully synced new contact message (ID: {model_instance.id}) to Flask database')
            
    except Exception as e:
        logger.error(f'Error syncing {model_type} to Flask: {str(e)}')
        raise

# Add a signal handler for user creation
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def sync_user_on_save(sender, instance, created, **kwargs):
    """
    Signal handler to sync user when created or updated
    """
    try:
        sync_user_to_flask(instance)
        logger.info(f'Successfully synced user {instance.username} to Flask database')
    except Exception as e:
        logger.error(f'Error syncing user {instance.username} to Flask: {str(e)}')

# Add a signal handler for user login
from django.contrib.auth.signals import user_logged_in

@receiver(user_logged_in)
def sync_user_on_login(sender, request, user, **kwargs):
    """
    Signal handler to sync user on login
    """
    try:
        sync_user_to_flask(user)
        logger.info(f'Successfully synced logged-in user {user.username} to Flask database')
    except Exception as e:
        logger.error(f'Error syncing logged-in user {user.username} to Flask: {str(e)}')

def home_view(request):

    published_jobs = Job.objects.filter(is_published=True).order_by('-timestamp')
    jobs = published_jobs.filter(is_closed=False)
    total_candidates = User.objects.filter(role='employee').count()
    total_companies = User.objects.filter(role='employer').count()
    paginator = Paginator(jobs, 3)
    page_number = request.GET.get('page',None)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

        job_lists=[]
        job_objects_list = page_obj.object_list.values()
        for job_list in job_objects_list:
            job_lists.append(job_list)
        

        next_page_number = None
        if page_obj.has_next():
            next_page_number = page_obj.next_page_number()

        prev_page_number = None       
        if page_obj.has_previous():
            prev_page_number = page_obj.previous_page_number()

        data={
            'job_lists':job_lists,
            'current_page_no':page_obj.number,
            'next_page_number':next_page_number,
            'no_of_page':paginator.num_pages,
            'prev_page_number':prev_page_number
        }    
        return JsonResponse(data)
    
    context = {

    'total_candidates': total_candidates,
    'total_companies': total_companies,
    'total_jobs': len(jobs),
    'total_completed_jobs':len(published_jobs.filter(is_closed=True)),
    'page_obj': page_obj
    }
    print('ok')
    return render(request, 'jobapp/index.html', context)

def job_list_View(request):
    """
    """
    job_list = Job.objects.filter(is_published=True,is_closed=False).order_by('-timestamp')
    paginator = Paginator(job_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'jobapp/job-list.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def create_job_View(request):
    """
    Create job post directly in Flask database
    """
    form = JobForm(request.POST or None)
    user = get_object_or_404(User, id=request.user.id)
    categories = Category.objects.all()

    if request.method == 'POST':
        if form.is_valid():
            try:
                # Save to Flask database
                job_data = {
                    'title': form.cleaned_data['title'],
                    'company': form.cleaned_data['company_name'],
                    'description': form.cleaned_data['description'],
                    'location': form.cleaned_data['location'],
                    'salary': form.cleaned_data.get('salary', ''),
                    'experience': form.cleaned_data.get('experience', ''),
                    'department': form.cleaned_data.get('department', ''),
                    'company_type': form.cleaned_data.get('company_type', ''),
                    'work_mode': form.cleaned_data.get('work_mode', ''),
                    'date_posted': datetime.now().strftime('%Y-%m-%d')
                }
                flask_job = save_to_flask('job', job_data)
                
                # Also save to Django for compatibility
                instance = form.save(commit=False)
                instance.user = user
                instance.is_published = True
                instance.save()
                form.save_m2m()
                
                messages.success(request, 'Your job has been successfully posted!')
                return redirect(reverse("jobapp:single-job", kwargs={'id': instance.id}))
            except Exception as e:
                messages.error(request, f'Error creating job: {str(e)}')
                logger.error(f'Error creating job: {str(e)}')

    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'jobapp/post-job.html', context)


@login_required
@user_is_employee
def rate_job_view(request, id):
    job = get_object_or_404(Job, id=id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        # Check if user has already rated this job
        existing_rating = JobRating.objects.filter(user=request.user, job=job).first()
        
        if existing_rating:
            existing_rating.rating = rating
            existing_rating.comment = comment
            existing_rating.save()
            messages.success(request, 'Your rating has been updated successfully!')
        else:
            JobRating.objects.create(
                user=request.user,
                job=job,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Thank you for rating this job!')
        
        return redirect(reverse('jobapp:single-job', kwargs={'id': id}))
    
    return redirect(reverse('jobapp:single-job', kwargs={'id': id}))

def single_job_view(request, id):
    """
    Provide the ability to view job details
    """
    if cache.get(id):
        job = cache.get(id)
    else:
        job = get_object_or_404(Job, id=id)
        cache.set(id, job, 60 * 15)
    
    related_job_list = job.tags.similar_objects()
    user_rating = None
    if request.user.is_authenticated and request.user.role == 'employee':
        user_rating = JobRating.objects.filter(user=request.user, job=job).first()

    paginator = Paginator(related_job_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'job': job,
        'page_obj': page_obj,
        'total': len(related_job_list),
        'user_rating': user_rating,
        'average_rating': job.get_average_rating(),
        'rating_count': job.get_rating_count()
    }
    return render(request, 'jobapp/job-single.html', context)


def search_result_view(request):
    """
        User can search job with multiple fields

    """

    job_list = Job.objects.order_by('-timestamp')

    # Keywords
    if 'job_title_or_company_name' in request.GET:
        job_title_or_company_name = request.GET['job_title_or_company_name']

        if job_title_or_company_name:
            job_list = job_list.filter(title__icontains=job_title_or_company_name) | job_list.filter(
                company_name__icontains=job_title_or_company_name)

    # location
    if 'location' in request.GET:
        location = request.GET['location']
        if location:
            job_list = job_list.filter(location__icontains=location)

    # Job Type
    if 'job_type' in request.GET:
        job_type = request.GET['job_type']
        if job_type:
            job_list = job_list.filter(job_type__iexact=job_type)

    # job_title_or_company_name = request.GET.get('text')
    # location = request.GET.get('location')
    # job_type = request.GET.get('type')

    #     job_list = Job.objects.all()
    #     job_list = job_list.filter(
    #         Q(job_type__iexact=job_type) |
    #         Q(title__icontains=job_title_or_company_name) |
    #         Q(location__icontains=location)
    #     ).distinct()

    # job_list = Job.objects.filter(job_type__iexact=job_type) | Job.objects.filter(
    #     location__icontains=location) | Job.objects.filter(title__icontains=text) | Job.objects.filter(company_name__icontains=text)

    paginator = Paginator(job_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {

        'page_obj': page_obj,

    }
    return render(request, 'jobapp/result.html', context)


@login_required
def apply_job_view(request, id):
    job = get_object_or_404(Job, id=id)
    
    # Check if user has already applied
    if Applicant.objects.filter(user=request.user, job=job).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect(reverse('jobapp:single-job', kwargs={'id': id}))
    
    if request.method == 'POST':
        form = JobApplyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # First ensure user exists in Flask database
                flask_user = FlaskUser.objects.using('flaskdb').filter(email=request.user.email).first()
                if not flask_user:
                    flask_user = FlaskUser.objects.using('flaskdb').create(
                        username=request.user.email,
                        email=request.user.email,
                        mobile=request.user.mobile or '',
                        role=request.user.role,
                        password_hash=''  # Empty password hash since we don't need it for applications
                    )
                
                # Then ensure job exists in Flask database
                flask_job = FlaskJob.objects.using('flaskdb').filter(title=job.title, company=job.company_name).first()
                if not flask_job:
                    flask_job = FlaskJob.objects.using('flaskdb').create(
                        title=job.title,
                        company=job.company_name,
                        experience='',
                        salary=job.salary or '',
                        location=job.location,
                        department='',
                        company_type='',
                        work_mode='',
                        description=job.description,
                        date_posted=job.timestamp.strftime('%Y-%m-%d')
                    )
                
                # Now create the application with correct Flask IDs
                application_data = {
                    'user_id': flask_user.id,
                    'job_id': flask_job.id,
                    'status': 'Pending',
                    'cover_letter': form.cleaned_data.get('cover_letter', ''),
                    'date_applied': datetime.now()
                }
                flask_application = save_to_flask('application', application_data)
                
                # Also save to Django for compatibility
                application = form.save(commit=False)
                application.user = request.user
                application.job = job
                application.status = 'pending'
                application.save()
                
                messages.success(request, 'Your application has been submitted successfully!')
                return redirect(reverse('jobapp:single-job', kwargs={'id': id}))
            except Exception as e:
                messages.error(request, f'Error submitting application: {str(e)}')
                logger.error(f'Error submitting application: {str(e)}')
    else:
        form = JobApplyForm(initial={'job': job})
    
    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'jobapp/apply-job.html', context)


@login_required(login_url=reverse_lazy('account:login'))
def dashboard_view(request):
    # Redirect admins to the admin dashboard
    if request.user.is_superuser or request.user.is_staff:
        return redirect('jobapp:admin-dashboard')
    jobs = []
    savedjobs = []
    appliedjobs = []
    total_applicants = {}
    if request.user.role == 'employer':
        jobs = Job.objects.filter(user=request.user.id)
        for job in jobs:
            count = Applicant.objects.filter(job=job.id).count()
            total_applicants[job.id] = count
    if request.user.role == 'employee':
        savedjobs = BookmarkJob.objects.filter(user=request.user.id)
        appliedjobs = Applicant.objects.filter(user=request.user.id)
    context = {
        'jobs': jobs,
        'savedjobs': savedjobs,
        'appliedjobs':appliedjobs,
        'total_applicants': total_applicants
    }
    return render(request, 'jobapp/dashboard.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def delete_job_view(request, id):
    try:
        job = get_object_or_404(Job, id=id, user=request.user)
        
        # Delete from Flask first
        try:
            FlaskJob.objects.using('flaskdb').filter(django_job_id=job.id).delete()
            logger.info(f'Deleted Flask job with Django job ID {job.id}')
        except Exception as e:
            logger.error(f'Error deleting Flask job: {str(e)}')
            messages.warning(request, 'Job was deleted from Django but could not be deleted from Flask database.')
        
        # Then delete from Django
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('jobapp:dashboard')
    except Exception as e:
        messages.error(request, 'Something went wrong while deleting the job. Please try again.')
        return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def make_complete_job_view(request, id):
    job = get_object_or_404(Job, id=id, user=request.user.id)

    if job:
        try:
            job.is_closed = True
            job.save()
            messages.success(request, 'Your Job was marked closed!')
        except:
            messages.success(request, 'Something went wrong !')
            
    return redirect('jobapp:dashboard')



@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def all_applicants_view(request, id):

    all_applicants = Applicant.objects.filter(job=id)

    context = {

        'all_applicants': all_applicants
    }

    return render(request, 'jobapp/all-applicants.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def delete_bookmark_view(request, id):

    job = get_object_or_404(BookmarkJob, id=id, user=request.user.id)

    if job:

        job.delete()
        messages.success(request, 'Saved Job was successfully deleted!')

    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def applicant_details_view(request, id):

    applicant = get_object_or_404(User, id=id)

    context = {

        'applicant': applicant
    }

    return render(request, 'jobapp/applicant-details.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def job_bookmark_view(request, id):

    form = JobBookmarkForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    applicant = BookmarkJob.objects.filter(user=request.user.id, job=id)

    if not applicant:
        if request.method == 'POST':

            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user
                instance.save()

                messages.success(
                    request, 'You have successfully save this job!')
                return redirect(reverse("jobapp:single-job", kwargs={
                    'id': id
                }))

        else:
            return redirect(reverse("jobapp:single-job", kwargs={
                'id': id
            }))

    else:
        messages.error(request, 'You already saved this Job!')

        return redirect(reverse("jobapp:single-job", kwargs={
            'id': id
        }))


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def job_edit_view(request, id=id):
    """
    Handle Job Update
    """
    job = get_object_or_404(Job, id=id, user=request.user.id)
    categories = Category.objects.all()
    form = JobEditForm(request.POST or None, instance=job)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        # for save tags
        # form.save_m2m()
        
        # Sync the updated job to Flask
        try:
            sync_to_flask(instance, 'job')
            messages.success(request, 'Your Job Post Was Successfully Updated and Synced!')
        except Exception as e:
            messages.warning(request, 'Job was updated in Django but could not be synced to Flask database.')
            logger.error(f'Error syncing job to Flask: {str(e)}')
            
        return redirect(reverse("jobapp:single-job", kwargs={
            'id': instance.id
        }))
    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'jobapp/job-edit.html', context)

@login_required
@user_is_employee
def remove_application_view(request, id):
    try:
        # Try Django application first
        try:
            # Get the application directly using the ID
            application = get_object_or_404(Applicant, id=id)
            # Verify the user owns this application
            if application.user.id != request.user.id:
                messages.error(request, 'You are not authorized to remove this application.')
                return redirect('jobapp:dashboard')
            application.delete()
            messages.success(request, 'Application removed successfully!')
            logger.info(f'Successfully removed Django application {id}')
        except Http404:
            # If not found in Django, try Flask application
            try:
                flask_application = FlaskJobApplication.objects.using('flaskdb').get(id=id)
                # Verify the user owns this application
                if flask_application.user_id != request.user.id:
                    messages.error(request, 'You are not authorized to remove this application.')
                    return redirect('jobapp:dashboard')
                flask_application.delete()
                messages.success(request, 'Application removed successfully!')
                logger.info(f'Successfully removed Flask application {id}')
            except FlaskJobApplication.DoesNotExist:
                messages.error(request, 'Application not found!')
                logger.error(f'Application {id} not found in either Django or Flask database')
    except Exception as e:
        messages.error(request, f'Error removing application: {str(e)}')
        logger.error(f'Error removing application {id}: {str(e)}')
    
    return redirect('jobapp:dashboard')

def about_us_view(request):
    print("about_us_view called")  # Debug: confirm this view is being used
    try:
        response = requests.get('http://127.0.0.1:5000/api/about-us')
        about = response.json()
        print("Flask API response:", about)  # Debug: show API response
    except Exception as e:
        about = {"title": "About Us", "content": f"Could not fetch About Us info. Error: {e}"}
        print("Error fetching from Flask API:", e)  # Debug: show error
    return render(request, 'jobapp/about-us.html', {'about': about})

@login_required(login_url=reverse_lazy('account:login'))
def contact_us_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject', '')
        message = request.POST.get('message')
        if name and email and message:
            try:
                # Save to Flask database
                contact_data = {
                    'name': name,
                    'email': email,
                    'subject': subject,
                    'message': message
                }
                flask_contact = save_to_flask('contact', contact_data)
                
                # Also save to Django for compatibility
                contact = Contact.objects.create(
                    name=name,
                    email=email,
                    subject=subject,
                    message=message
                )
                
                messages.success(request, "Message sent successfully!")
                return redirect('jobapp:contact-us')
            except Exception as e:
                messages.error(request, f'Error sending message: {str(e)}')
                logger.error(f'Error sending message: {str(e)}')
        else:
            messages.error(request, "All fields are required.")
    return render(request, 'jobapp/contact-us.html', {})

@login_required(login_url=reverse_lazy('account:login'))
def superuser_dashboard_view(request):
    if not request.user.is_superuser:
        logger.warning(f'Unauthorized access attempt to admin dashboard by user {request.user.username}')
        return redirect('home')
    
    logger.info(f'Admin dashboard accessed by {request.user.username}')
    
    # Get Django contact messages
    contact_messages = Contact.objects.all().order_by('-timestamp')
    logger.info(f'Found {contact_messages.count()} Django contact messages')
    
    # Get Django job applications
    django_applications = Applicant.objects.all().order_by('-timestamp')
    logger.info(f'Found {django_applications.count()} Django job applications')
    
    # Initialize Flask-related variables
    flask_contact_messages = []
    flask_applications = []
    
    try:
        # Get Flask contact messages from API
        logger.info('Fetching Flask contact messages')
        response = requests.get('http://127.0.0.1:5000/api/contact-messages', timeout=5)
        if response.status_code == 200:
            flask_contact_messages = response.json()
            logger.info(f'Successfully fetched {len(flask_contact_messages)} Flask contact messages')
        else:
            logger.warning(f'Failed to fetch Flask contact messages. Status code: {response.status_code}')
            messages.warning(request, f'Could not fetch Flask contact messages. Status code: {response.status_code}')
        
        # Get Flask job applications from API
        logger.info('Fetching Flask job applications')
        response = requests.get('http://127.0.0.1:5000/api/job-applications', timeout=5)
        if response.status_code == 200:
            flask_applications = response.json()
            logger.info(f'Successfully fetched {len(flask_applications)} Flask job applications')
        else:
            logger.warning(f'Failed to fetch Flask job applications. Status code: {response.status_code}')
            messages.warning(request, f'Could not fetch Flask job applications. Status code: {response.status_code}')
    except requests.exceptions.ConnectionError:
        logger.error('Connection error while fetching Flask data')
        messages.error(request, 'Could not connect to Flask server. Please ensure it is running.')
    except requests.exceptions.Timeout:
        logger.error('Timeout while fetching Flask data')
        messages.error(request, 'Request to Flask server timed out.')
    except Exception as e:
        logger.error(f'Error fetching Flask data: {str(e)}')
        messages.error(request, f'Error fetching Flask data: {str(e)}')
    
    # Calculate statistics for the dashboard
    total_ratings = JobRating.objects.count()
    jobs_with_ratings = Job.objects.filter(ratings__isnull=False).distinct().count()
    average_rating = JobRating.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get top rated jobs
    top_rated_jobs = Job.objects.annotate(
        avg_rating=Avg('ratings__rating')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:5]
    
    context = {
        'contact_messages': contact_messages,
        'flask_contact_messages': flask_contact_messages,
        'django_applications': django_applications,
        'flask_applications': flask_applications,
        'total_ratings': total_ratings,
        'jobs_with_ratings': jobs_with_ratings,
        'average_rating': round(average_rating, 1),
        'top_rated_jobs': top_rated_jobs,
        'has_messages': contact_messages.exists() or bool(flask_contact_messages),
        'has_applications': django_applications.exists() or bool(flask_applications),
        'has_flask_messages': bool(flask_contact_messages),
        'has_django_messages': contact_messages.exists(),
    }
    
    return render(request, 'jobapp/superuser-dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def view_application(request, application_id):
    try:
        # Try Django application first
        application = Applicant.objects.get(id=application_id)
        is_flask = False
    except Applicant.DoesNotExist:
        try:
            # Try Flask application
            application = FlaskJobApplication.objects.using('flaskdb').get(id=application_id)
            print(f"Flask Application: {application.__dict__}")  # Debug print
            print(f"Looking up FlaskUser with id={application.user_id}")
            try:
                flask_user = FlaskUser.objects.using('flaskdb').get(id=application.user_id)
                print(f"Flask User: {flask_user.__dict__}")  # Debug print
            except Exception as e:
                print(f"FlaskUser lookup failed: {e}")
                flask_user = None
            print(f"Looking up FlaskJob with id={application.job_id}")
            try:
                flask_job = FlaskJob.objects.using('flaskdb').get(id=application.job_id)
                print(f"Flask Job: {flask_job.__dict__}")  # Debug print
            except Exception as e:
                print(f"FlaskJob lookup failed: {e}")
                flask_job = None
            # Add user and job details to the application object
            if flask_user:
                application.name = flask_user.username
                application.email = flask_user.email
                application.phone = flask_user.mobile
                print(f"Set application.name={application.name}, email={application.email}, phone={application.phone}")
            else:
                application.name = application.email = application.phone = None
            if flask_job:
                application.job_title = flask_job.title
                application.company = flask_job.company
                print(f"Set application.job_title={application.job_title}, company={application.company}")
            else:
                application.job_title = application.company = None
            is_flask = True
        except (FlaskJobApplication.DoesNotExist) as e:
            print(f"Error: {str(e)}")  # Debug print
            messages.error(request, 'Application not found')
            return redirect('jobapp:admin-dashboard')
    context = {
        'application': application,
        'is_flask': is_flask
    }
    return render(request, 'jobapp/application-detail.html', context)

@login_required(login_url=reverse_lazy('account:login'))
def view_resume(request, application_id):
    """
    View applicant's resume
    """
    if not request.user.is_superuser:
        raise Http404("You don't have permission to access this page")
    
    application = get_object_or_404(Applicant, id=application_id)
    
    if not application.resume:
        messages.error(request, 'No resume found for this application')
        return redirect('jobapp:admin-dashboard')
    
    try:
        with open(application.resume.path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline;filename={application.resume.name}'
            return response
    except:
        messages.error(request, 'Error opening resume file')
        return redirect('jobapp:admin-dashboard')

@login_required(login_url=reverse_lazy('account:login'))
def delete_test_message(request):
    """
    Delete the test contact message
    """
    if not request.user.is_superuser:
        raise Http404("You don't have permission to access this page")
    
    Contact.objects.filter(
        name="Test User",
        email="test@example.com",
        subject="Test Message"
    ).delete()
    
    messages.success(request, 'Test message has been removed successfully!')
    return redirect('jobapp:admin-dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_application_status(request, application_id, status):
    if not request.user.is_superuser:
        return redirect('home')
    
    try:
        # Try Django application first
        application = Applicant.objects.get(id=application_id)
        application.status = status
        application.save()
        
        # Sync status change to Flask
        try:
            sync_to_flask(application, 'application')
            messages.success(request, f'Application status updated to {status} and synced!')
        except Exception as e:
            messages.warning(request, f'Status was updated in Django but could not be synced to Flask database.')
            logger.error(f'Error syncing application status to Flask: {str(e)}')
            
    except Applicant.DoesNotExist:
        try:
            # Try Flask application through API
            flask_status = 'Accepted' if status == 'shortlisted' else 'Rejected'
            response = requests.post(
                f'http://127.0.0.1:5000/api/update-application-status/{application_id}',
                json={'status': flask_status},
                timeout=5
            )
            if response.status_code == 200:
                messages.success(request, f'Application status updated to {status}')
                logger.info(f'Successfully updated Flask application {application_id} status to {flask_status}')
            else:
                error_msg = response.json().get('error', 'Unknown error')
                messages.error(request, f'Failed to update application status: {error_msg}')
                logger.error(f'Failed to update Flask application status. Status code: {response.status_code}, Error: {error_msg}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error updating application status: {str(e)}')
            logger.error(f'Request error while updating Flask application status: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error updating application status: {str(e)}')
            logger.error(f'Unexpected error while updating Flask application status: {str(e)}')
    
    return redirect('jobapp:admin-dashboard')

@login_required(login_url=reverse_lazy('account:login'))
def view_flask_application(request, application_id):
    if not request.user.is_superuser:
        return redirect('home')
    
    try:
        application = FlaskJobApplication.objects.using('flaskdb').get(id=application_id)
        context = {
            'application': application,
            'is_flask': True
        }
        return render(request, 'jobapp/application-detail.html', context)
    except FlaskJobApplication.DoesNotExist:
        messages.error(request, 'Application not found')
        return redirect('jobapp:admin-dashboard')

def job_list_api_view(request):
    """
    API endpoint that returns a list of jobs in JSON format
    """
    print("API endpoint called")  # Debug print
    try:
        job_list = Job.objects.filter(is_published=True, is_closed=False).order_by('-timestamp')
        print(f"Found {job_list.count()} jobs")  # Debug print
        
        jobs_data = []
        for job in job_list:
            job_data = {
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'location': job.location,
                'job_type': job.job_type,
                'company_name': job.company_name,
                'company_description': job.company_description,
                'website': job.website,
                'created_at': job.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'is_published': job.is_published,
                'is_closed': job.is_closed
            }
            jobs_data.append(job_data)
        
        print(f"Returning {len(jobs_data)} jobs")  # Debug print
        response = JsonResponse({
            'status': 'success',
            'jobs': jobs_data
        })
        response['Content-Type'] = 'application/json'
        response['Access-Control-Allow-Origin'] = '*'  # Allow all origins
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    except Exception as e:
        print(f"Error in API: {str(e)}")  # Debug print
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
