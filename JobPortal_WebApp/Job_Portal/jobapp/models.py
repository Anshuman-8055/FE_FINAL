from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
User = get_user_model()

from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager

JOB_TYPE = (
    ('1', "Full time"),
    ('2', "Part time"),
    ('3', "Internship"),
)

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Job(models.Model):
    user = models.ForeignKey(User, related_name='User', on_delete=models.CASCADE) 
    title = models.CharField(max_length=300)
    description = RichTextField()
    tags = TaggableManager()
    location = models.CharField(max_length=300)
    job_type = models.CharField(choices=JOB_TYPE, max_length=1)
    category = models.ForeignKey(Category, related_name='Category', on_delete=models.SET_NULL, null=True, blank=True)  # ✅ Allow Null and Blank
    salary = models.CharField(max_length=30, blank=True)
    company_name = models.CharField(max_length=300)
    company_description = RichTextField(blank=True, null=True)
    url = models.URLField(max_length=200)
    last_date = models.DateField()
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_average_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return round(sum(rating.rating for rating in ratings) / len(ratings), 1)
        return 0

    def get_rating_count(self):
        return self.ratings.count()

class Applicant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    cover_letter = RichTextField(help_text='Write your cover letter here', null=True, blank=True)
    resume = models.FileField(upload_to='resumes/', help_text='Upload your resume', null=True, blank=True)
    experience = models.TextField(help_text='Describe your relevant experience', null=True, blank=True)
    skills = models.TextField(help_text='List your relevant skills', null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('reviewed', 'Reviewed'),
            ('shortlisted', 'Shortlisted'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.job.title}"

class BookmarkJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return self.job.title

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

class JobRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 star rating
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')  # One rating per user per job

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.job.title} - {self.rating} stars"

class FlaskContactMessage(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    date_submitted = models.DateTimeField()

    class Meta:
        db_table = 'contact'
        managed = False

    def save(self, *args, **kwargs):
        kwargs['using'] = 'flaskdb'
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        kwargs['using'] = 'flaskdb'
        super().delete(*args, **kwargs)

    @classmethod
    def objects(cls):
        return super().objects.using('flaskdb')
