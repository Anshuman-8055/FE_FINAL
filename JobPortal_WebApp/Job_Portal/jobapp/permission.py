from django.core.exceptions import PermissionDenied

def user_is_employer(function):

    def wrap(request, *args, **kwargs):   

        if request.user.role == 'employer':
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrap



def user_is_employee(function):

    def wrap(request, *args, **kwargs):    
        if not request.user.role:
            print(f"Error: User {request.user.email} has no role assigned")
            raise PermissionDenied("User has no role assigned. Please contact administrator.")
        
        if request.user.role == 'employee':
            return function(request, *args, **kwargs)
        else:
            print(f"Permission denied: User {request.user.email} has role '{request.user.role}', expected 'employee'")
            raise PermissionDenied(f"Only employees can access this page. Your role is '{request.user.role}'")

    return wrap