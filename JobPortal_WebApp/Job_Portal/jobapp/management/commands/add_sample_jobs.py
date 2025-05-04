from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from jobapp.models import Job, Category
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Adds sample jobs to the database'

    def handle(self, *args, **kwargs):
        # Create categories if they don't exist
        categories = ['Technology', 'Finance', 'Healthcare', 'Education', 'Marketing']
        for category_name in categories:
            Category.objects.get_or_create(name=category_name)

        # Get the first superuser
        employer = User.objects.filter(is_superuser=True).first()
        if not employer:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return

        # Sample jobs data
        jobs_data = [
            {
                'title': 'Senior Python Developer',
                'description': 'We are looking for an experienced Python developer to join our team. The ideal candidate should have strong experience with Django, REST APIs, and database design.',
                'location': 'New York, NY',
                'job_type': '1',  # Full time
                'category': 'Technology',
                'salary': '$120,000 - $150,000',
                'company_name': 'Tech Solutions Inc.',
                'company_description': 'A leading technology company specializing in enterprise software solutions.',
                'url': 'https://techsolutions.com',
                'last_date': datetime.now() + timedelta(days=30),
                'is_published': True,
                'tags': ['python', 'django', 'rest-api', 'postgresql']
            },
            {
                'title': 'Financial Analyst',
                'description': 'Seeking a financial analyst to help with financial planning, analysis, and reporting. Experience with financial modeling and Excel required.',
                'location': 'Chicago, IL',
                'job_type': '1',  # Full time
                'category': 'Finance',
                'salary': '$80,000 - $100,000',
                'company_name': 'Global Finance Corp',
                'company_description': 'A multinational financial services company.',
                'url': 'https://globalfinance.com',
                'last_date': datetime.now() + timedelta(days=45),
                'is_published': True,
                'tags': ['finance', 'excel', 'financial-modeling', 'analysis']
            },
            {
                'title': 'Marketing Intern',
                'description': 'Looking for a creative and motivated marketing intern to assist with social media management, content creation, and marketing campaigns.',
                'location': 'Los Angeles, CA',
                'job_type': '3',  # Internship
                'category': 'Marketing',
                'salary': '$20/hour',
                'company_name': 'Creative Marketing Agency',
                'company_description': 'A dynamic marketing agency focused on digital marketing solutions.',
                'url': 'https://creativemarketing.com',
                'last_date': datetime.now() + timedelta(days=20),
                'is_published': True,
                'tags': ['marketing', 'social-media', 'content-creation', 'internship']
            },
            {
                'title': 'Registered Nurse',
                'description': 'Seeking a compassionate and skilled registered nurse to join our healthcare team. Must have valid RN license and 2+ years of experience.',
                'location': 'Boston, MA',
                'job_type': '2',  # Part time
                'category': 'Healthcare',
                'salary': '$35 - $45/hour',
                'company_name': 'Boston Medical Center',
                'company_description': 'A leading healthcare provider in the Boston area.',
                'url': 'https://bostonmedical.com',
                'last_date': datetime.now() + timedelta(days=15),
                'is_published': True,
                'tags': ['nursing', 'healthcare', 'patient-care', 'medical']
            },
            {
                'title': 'High School Teacher',
                'description': 'Looking for an enthusiastic high school teacher to teach mathematics. Must have teaching certification and experience with high school students.',
                'location': 'Seattle, WA',
                'job_type': '1',  # Full time
                'category': 'Education',
                'salary': '$50,000 - $65,000',
                'company_name': 'Seattle Public Schools',
                'company_description': 'A public school district committed to providing quality education.',
                'url': 'https://seattleschools.edu',
                'last_date': datetime.now() + timedelta(days=25),
                'is_published': True,
                'tags': ['teaching', 'education', 'mathematics', 'high-school']
            }
        ]

        # Create jobs
        for job_data in jobs_data:
            category = Category.objects.get(name=job_data.pop('category'))
            tags = job_data.pop('tags')
            
            job = Job.objects.create(
                user=employer,
                category=category,
                **job_data
            )
            job.tags.add(*tags)
            
            self.stdout.write(self.style.SUCCESS(f'Created job: {job.title}'))

        self.stdout.write(self.style.SUCCESS('Successfully added sample jobs')) 