from django.db import migrations
from django.utils import timezone
from datetime import timedelta

def add_sample_jobs(apps, schema_editor):
    Job = apps.get_model('jobapp', 'Job')
    Category = apps.get_model('jobapp', 'Category')
    User = apps.get_model('account', 'User')

    # Create a default admin user if it doesn't exist
    admin_user, _ = User.objects.get_or_create(
        email='admin@example.com',
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'role': 'employer',
            'first_name': 'Admin',
            'last_name': 'User',
            'gender': 'M',
            'password': 'admin123'  # This is a temporary password
        }
    )

    # Create some categories if they don't exist
    categories = {
        'Technology': Category.objects.get_or_create(name='Technology')[0],
        'Finance': Category.objects.get_or_create(name='Finance')[0],
        'Healthcare': Category.objects.get_or_create(name='Healthcare')[0],
        'Education': Category.objects.get_or_create(name='Education')[0],
    }

    # Sample jobs data
    sample_jobs = [
        {
            'title': 'Senior Software Engineer',
            'description': 'We are looking for an experienced software engineer to join our team. The ideal candidate should have strong problem-solving skills and experience with modern web technologies.',
            'location': 'New York, NY',
            'job_type': '1',  # Full time
            'salary': '$120,000 - $150,000',
            'company_name': 'TechCorp Solutions',
            'company_description': 'A leading technology company specializing in innovative software solutions.',
            'url': 'https://techcorp.com',
            'last_date': timezone.now() + timedelta(days=30),
            'is_published': True,
            'category': categories['Technology']
        },
        {
            'title': 'Financial Analyst',
            'description': 'Seeking a detail-oriented financial analyst to help drive business decisions through data analysis and financial modeling.',
            'location': 'Chicago, IL',
            'job_type': '1',  # Full time
            'salary': '$80,000 - $100,000',
            'company_name': 'Global Finance Group',
            'company_description': 'A premier financial services company with a global presence.',
            'url': 'https://globalfinance.com',
            'last_date': timezone.now() + timedelta(days=45),
            'is_published': True,
            'category': categories['Finance']
        },
        {
            'title': 'Registered Nurse',
            'description': 'Looking for compassionate and skilled registered nurses to join our healthcare team. Must have valid RN license and 2+ years of experience.',
            'location': 'Los Angeles, CA',
            'job_type': '1',  # Full time
            'salary': '$70,000 - $90,000',
            'company_name': 'City Medical Center',
            'company_description': 'A state-of-the-art medical facility providing comprehensive healthcare services.',
            'url': 'https://citymedical.com',
            'last_date': timezone.now() + timedelta(days=60),
            'is_published': True,
            'category': categories['Healthcare']
        },
        {
            'title': 'High School Teacher',
            'description': 'Seeking passionate educators to join our team. Must have teaching certification and experience in secondary education.',
            'location': 'Boston, MA',
            'job_type': '1',  # Full time
            'salary': '$50,000 - $70,000',
            'company_name': 'Boston Public Schools',
            'company_description': 'A leading public school district committed to excellence in education.',
            'url': 'https://bostonpublicschools.org',
            'last_date': timezone.now() + timedelta(days=90),
            'is_published': True,
            'category': categories['Education']
        }
    ]

    # Create the jobs
    for job_data in sample_jobs:
        Job.objects.get_or_create(
            user=admin_user,
            title=job_data['title'],
            defaults={
                'description': job_data['description'],
                'location': job_data['location'],
                'job_type': job_data['job_type'],
                'salary': job_data['salary'],
                'company_name': job_data['company_name'],
                'company_description': job_data['company_description'],
                'url': job_data['url'],
                'last_date': job_data['last_date'],
                'is_published': job_data['is_published'],
                'category': job_data['category']
            }
        )

def remove_sample_jobs(apps, schema_editor):
    Job = apps.get_model('jobapp', 'Job')
    Job.objects.filter(user__email='admin@example.com').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('jobapp', '0015_job_is_closed'),
    ]

    operations = [
        migrations.RunPython(add_sample_jobs, remove_sample_jobs),
    ] 