from django import forms
from jobapp.models import *
from ckeditor.widgets import CKEditorWidget

class JobForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        self.fields['title'].label = "Job Title :"
        self.fields['location'].label = "Job Location :"
        self.fields['salary'].label = "Salary :"
        self.fields['description'].label = "Job Description :"
        self.fields['tags'].label = "Tags :"
        self.fields['last_date'].label = "Submission Deadline :"
        self.fields['company_name'].label = "Company Name :"
        self.fields['url'].label = "Website :"

        self.fields['title'].widget.attrs.update({
            'placeholder': 'eg : Software Developer',
        })        
        self.fields['location'].widget.attrs.update({
            'placeholder': 'eg : Bangladesh',
        })
        self.fields['salary'].widget.attrs.update({
            'placeholder': '$800 - $1200',
        })
        self.fields['tags'].widget.attrs.update({
            'placeholder': 'Use comma separated. eg: Python, JavaScript ',
        })                        
        self.fields['last_date'].widget.attrs.update({
            'placeholder': 'YYYY-MM-DD ',
        })        
        self.fields['company_name'].widget.attrs.update({
            'placeholder': 'Company Name',
        })           
        self.fields['url'].widget.attrs.update({
            'placeholder': 'https://example.com',
        })

    class Meta:
        model = Job
        fields = [
            "title",
            "location",
            "job_type",
            "salary",
            "description",
            "tags",
            "last_date",
            "company_name",
            "company_description",
            "url"
        ]

    def clean_job_type(self):
        job_type = self.cleaned_data.get('job_type')

        if not job_type:
            raise forms.ValidationError("Job Type is required")
        return job_type

    def save(self, commit=True):
        job = super(JobForm, self).save(commit=False)
        
        if not job.category:  # ✅ Assign default category if missing
            job.category = Category.objects.first() or Category.objects.create(name="General")  # Default category if no category selected
        
        if commit:
            job.save()
        return job

class JobApplyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        self.fields['cover_letter'].label = "Cover Letter :"
        self.fields['resume'].label = "Resume :"
        self.fields['experience'].label = "Experience :"
        self.fields['skills'].label = "Skills :"

        self.fields['cover_letter'].widget.attrs.update({
            'placeholder': 'Write your cover letter here...',
        })
        self.fields['experience'].widget.attrs.update({
            'placeholder': 'Describe your relevant experience...',
        })
        self.fields['skills'].widget.attrs.update({
            'placeholder': 'List your relevant skills...',
        })

    class Meta:
        model = Applicant
        fields = ['job', 'cover_letter', 'resume', 'experience', 'skills']
        widgets = {
            'job': forms.HiddenInput(),
        }

class JobBookmarkForm(forms.ModelForm):
    class Meta:
        model = BookmarkJob
        fields = ['job']

class JobEditForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        self.fields['title'].label = "Job Title :"
        self.fields['location'].label = "Job Location :"
        self.fields['salary'].label = "Salary :"
        self.fields['description'].label = "Job Description :"
        self.fields['last_date'].label = "Dead Line :"
        self.fields['company_name'].label = "Company Name :"
        self.fields['url'].label = "Website :"

        self.fields['title'].widget.attrs.update({
            'placeholder': 'eg : Software Developer',
        })        
        self.fields['location'].widget.attrs.update({
            'placeholder': 'eg : Bangladesh',
        })
        self.fields['salary'].widget.attrs.update({
            'placeholder': '$800 - $1200',
        })
        self.fields['last_date'].widget.attrs.update({
            'placeholder': 'YYYY-MM-DD ',
        })        
        self.fields['company_name'].widget.attrs.update({
            'placeholder': 'Company Name',
        })           
        self.fields['url'].widget.attrs.update({
            'placeholder': 'https://example.com',
        })

    class Meta:
        model = Job
        fields = [
            "title",
            "location",
            "job_type",
            "salary",
            "description",
            "last_date",
            "company_name",
            "company_description",
            "url"
        ]

    def clean_job_type(self):
        job_type = self.cleaned_data.get('job_type')

        if not job_type:
            raise forms.ValidationError("Job Type is required")
        return job_type

    def save(self, commit=True):
        job = super(JobEditForm, self).save(commit=False)
        if commit:
            job.save()
        return job
