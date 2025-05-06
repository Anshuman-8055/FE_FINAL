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

from account.models import User
from jobapp.forms import *
from jobapp.models import *
from jobapp.permission import *
from jobapp.models import Contact
from .models import Job, Applicant, Contact, JobRating, FlaskContactMessage, FlaskJobApplication, FlaskJob, FlaskUser
User = get_user_model()


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
    Provide the ability to create job post
    """
    form = JobForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    categories = Category.objects.all()

    if request.method == 'POST':

        if form.is_valid():

            instance = form.save(commit=False)
            instance.user = user
            instance.is_published = True  # Automatically publish the job
            instance.save()
            # for save tags
            form.save_m2m()
            messages.success(
                    request, 'Your job has been successfully posted!')
            return redirect(reverse("jobapp:single-job", kwargs={
                                    'id': instance.id
                                    }))

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
            application = form.save(commit=False)
            application.user = request.user
            application.job = job
            application.status = 'pending'
            application.save()
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect(reverse('jobapp:single-job', kwargs={'id': id}))
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
        messages.success(request, 'Your Job Post Was Successfully Updated!')
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
    job = get_object_or_404(Job, id=id)
    application = get_object_or_404(Applicant, user=request.user, job=job)
    application.delete()
    messages.success(request, 'Your application has been removed successfully!')
    return redirect(reverse('jobapp:single-job', kwargs={'id': id}))

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
    result = None
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject', '')  # If you have a subject field
        message = request.POST.get('message')
        if name and email and message:
            Contact.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, "Message sent!")
            return redirect('jobapp:contact-us')
        else:
            messages.error(request, "All fields are required.")
    return render(request, 'jobapp/contact-us.html', {'result': result})

@login_required(login_url=reverse_lazy('account:login'))
def superuser_dashboard_view(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    # Get Django contact messages
    contact_messages = Contact.objects.all().order_by('-timestamp')
    
    # Get Django job applications
    django_applications = Applicant.objects.all().order_by('-timestamp')
    
    # Initialize Flask-related variables
    flask_contact_messages = []
    flask_applications = []
    flask_jobs = {}
    flask_users = {}
    
    try:
        # Get Flask contact messages
        flask_contact_messages = FlaskContactMessage.objects.using('flaskdb').all().order_by('-date_submitted')
        
        # Get Flask job applications with related job and user info
        flask_applications = FlaskJobApplication.objects.using('flaskdb').all().order_by('-date_applied')
        
        # Get job and user info for Flask applications
        for app in flask_applications:
            if app.job_id not in flask_jobs:
                try:
                    job = FlaskJob.objects.using('flaskdb').get(id=app.job_id)
                    flask_jobs[app.job_id] = job
                except FlaskJob.DoesNotExist:
                    flask_jobs[app.job_id] = None
    except Exception as e:
        messages.warning(request, f'Could not load Flask data: {str(e)}')
    
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
        'flask_jobs': flask_jobs,
        'total_ratings': total_ratings,
        'jobs_with_ratings': jobs_with_ratings,
        'average_rating': round(average_rating, 1),
        'top_rated_jobs': top_rated_jobs,
        'has_messages': contact_messages.exists() or flask_contact_messages.exists(),
        'has_applications': django_applications.exists() or flask_applications.exists(),
        'has_flask_messages': flask_contact_messages.exists(),
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

@login_required(login_url=reverse_lazy('account:login'))
def update_application_status(request, application_id, status):
    if not request.user.is_superuser:
        return redirect('home')
    
    try:
        # Try Django application first
        application = Applicant.objects.get(id=application_id)
        application.status = status
        application.save()
        messages.success(request, f'Application status updated to {status}')
    except Applicant.DoesNotExist:
        try:
            # Try Flask application
            application = FlaskJobApplication.objects.using('flaskdb').get(id=application_id)
            if status == 'shortlisted':
                application.status = 'Accepted'
            elif status == 'rejected':
                application.status = 'Rejected'
            application.save()
            messages.success(request, f'Application status updated to {status}')
        except FlaskJobApplication.DoesNotExist:
            messages.error(request, 'Application not found')
    
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
