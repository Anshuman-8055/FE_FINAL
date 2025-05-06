from django.contrib import admin
from .models import *


admin.site.register(Category)

class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('job','user','timestamp')
    
admin.site.register(Applicant,ApplicantAdmin)


class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'is_closed', 'get_average_rating', 'get_rating_count', 'timestamp')
    readonly_fields = ('get_average_rating', 'get_rating_count')

    def get_average_rating(self, obj):
        return obj.get_average_rating()
    get_average_rating.short_description = 'Average Rating'

    def get_rating_count(self, obj):
        return obj.get_rating_count()
    get_rating_count.short_description = 'Rating Count'

admin.site.register(Job, JobAdmin)

class BookmarkJobAdmin(admin.ModelAdmin):
    list_display = ('job','user','timestamp')
admin.site.register(BookmarkJob,BookmarkJobAdmin)

class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'timestamp')
    search_fields = ('name', 'email', 'subject')
    list_filter = ('timestamp',)

admin.site.register(Contact, ContactAdmin)

class JobRatingAdmin(admin.ModelAdmin):
    list_display = ('job', 'user', 'rating', 'timestamp')
    list_filter = ('rating', 'timestamp')
    search_fields = ('job__title', 'user__email', 'comment')
    readonly_fields = ('timestamp',)

admin.site.register(JobRating, JobRatingAdmin)

class FlaskContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'date_submitted')
    search_fields = ('name', 'email', 'message')
    list_filter = ('date_submitted',)
    readonly_fields = ('date_submitted',)

admin.site.register(FlaskContactMessage, FlaskContactMessageAdmin)

@admin.register(FlaskJobApplication)
class FlaskJobApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'job_title', 'company', 'date_applied', 'status')
    list_filter = ('status', 'date_applied')
    search_fields = ('name', 'email', 'job_title', 'company')
    readonly_fields = ('date_applied',)
    ordering = ('-date_applied',)


