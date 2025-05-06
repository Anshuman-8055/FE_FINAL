class FlaskRouter:
    """
    Router to handle Flask models
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'jobapp' and hasattr(model, '_meta') and hasattr(model._meta, 'db_table'):
            if model._meta.db_table in ['contact', 'job_application', 'job', 'users']:
                return 'flaskdb'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'jobapp' and hasattr(model, '_meta') and hasattr(model._meta, 'db_table'):
            if model._meta.db_table in ['contact', 'job_application', 'job', 'users']:
                return 'flaskdb'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'jobapp':
            if model_name in ['flaskcontactmessage', 'flaskjobapplication', 'flaskjob', 'flaskuser']:
                return db == 'flaskdb'
        return None 