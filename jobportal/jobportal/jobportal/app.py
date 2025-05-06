from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, UserMixin, login_required, current_user
from datetime import datetime, date
from sqlalchemy import func
import functools
import re
import logging
import os
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "welcome"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/flask.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Job Portal startup')

db = SQLAlchemy(app)

# Create all database tables
try:
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
except Exception as e:
    print(f"Error creating database tables: {str(e)}")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(20), nullable=False)
    salary = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    company_type = db.Column(db.String(100), nullable=False)
    work_mode = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    reviews = db.Column(db.Integer, nullable=True)
    date_posted = db.Column(db.String(50), nullable=True)



class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    def save_hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_hash_password(self, password):
        return check_password_hash(self.password_hash, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Accepted, Rejected
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    gender = db.Column(db.String(10))
    dob = db.Column(db.String(20))
    experience = db.Column(db.String(200))
    
    # Relationships
    user = db.relationship('User', backref='applications')
    job = db.relationship('Job', backref='applications')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))

def is_strong_password(password):
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$', password))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        mobile = request.form.get("mobile")
        role = request.form.get("role") or "user"  # Default to 'user' if not checked

        # Password strength check
        if not is_strong_password(password):
            flash("Password must be at least 8 characters, include a capital letter, a small letter, and a number.", "danger")
            return redirect(url_for("register"))

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash("User already exists. Please log in.", "danger")
            return redirect(url_for("login"))

        # Create new user with role
        user_data = User(username=username, email=email, mobile=mobile, role=role)
        user_data.save_hash_password(password)

        # Save to database
        db.session.add(user_data)
        db.session.commit()

        flash("User registered successfully!", "success")
        if role == "admin":
            return redirect(url_for("login"))
        else:
            login_user(user_data)
            return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Password strength check
        if not is_strong_password(password):
            flash("Password must be at least 8 characters, include a capital letter, a small letter, and a number.", "danger")
            return redirect(url_for("login"))

        user_data = User.query.filter_by(email=email).first()

        if user_data and user_data.check_hash_password(password):
            login_user(user_data)
            flash("Logged in successfully!", "success")
            if user_data.role == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("home"))
        
        flash("Invalid email or password", "danger")

    return render_template("login.html")


jobs = [
    {
        "id": 1,
        "title": "Systems Analyst 1-IT",
        "company": "Oracle",
        "experience": "0-2",
        "salary": "Not disclosed",
        "location": "Kolkata, Mumbai",
        "tags": ["Training", "Oracle Apps", "Usage"],
        "rating": 3.7,
        "reviews": 5154,
        "description": "Provide support to internal users of Oracle Applications and legacy applications.",
        "posted_date": "3 Days Ago"
    },
    {
        "id": 2,
        "title": "Hiring Freshers | Service Desk Analyst",
        "company": "Wipro",
        "experience": "0",
        "salary": "Not disclosed",
        "location": "Bengaluru",
        "tags": ["Communication Skills", "English"],
        "rating": 3.7,
        "reviews": 52080,
        "description": "Shifts: 24*7 (5 days of work from office).",
        "posted_date": "1 Day Ago"
    },
    {
        "id": 3,
        "title": "Urgent opening For Site Reliability Engineer- Azure",
        "company": "HDFC Bank",
        "experience": "4-9",
        "salary": "5.5-13 Lacs PA",
        "location": "Gurugram, Bengaluru",
        "tags": ["Reliability Engineering", "Azure DevOps"],
        "rating": 3.9,
        "reviews": 38942,
        "description": "Minimum 4 years of experience in SRE role with strong knowledge of Azure.",
        "posted_date": "4 Days Ago"
    },
    # Add more job entries as needed
]


@app.route("/", methods=["GET"])
def home():
    # query = Job.query

    # experience = request.args.get("experience")
    # locations = request.args.getlist("location")
    # salaries = request.args.getlist("salary")
    # departments = request.args.getlist("department")
    # company_types = request.args.getlist("company_type")
    # work_modes = request.args.getlist("work_mode")

    # if experience:
    #     query = query.filter(Job.experience == experience)

    # if locations:
    #     query = query.filter(Job.location.in_(locations))

    # if salaries:
    #     query = query.filter(Job.salary.in_(salaries))

    # if departments:
    #     query = query.filter(Job.department.in_(departments))

    # if company_types:
    #     query = query.filter(Job.company_type.in_(company_types))

    # if work_modes:
    #     query = query.filter(Job.work_mode.in_(work_modes))

    # jobs = query.all()
    return render_template("index.html")


@app.route("/logout")
def logout():
    logout_user()
    flash("User  logged out successfully")
    return redirect(url_for("home"))


@app.route("/hero")
def hero():
    return render_template("hero.html") 

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('home'))

    jobs = Job.query.all()
    contacts = Contact.query.order_by(Contact.date_submitted.desc()).all()
    return render_template('admin.html', jobs=jobs, contacts=contacts)

@app.route('/admin/add-job', methods=['POST'])
@login_required
def add_job():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('home'))
    title = request.form.get('title')
    company = request.form.get('company')
    experience = request.form.get('experience')
    salary = request.form.get('salary')
    location = request.form.get('location')
    department = request.form.get('department')
    company_type = request.form.get('company_type')
    work_mode = request.form.get('work_mode')
    description = request.form.get('description')
    job = Job(title=title, company=company, experience=experience, salary=salary, location=location, department=department, company_type=company_type, work_mode=work_mode, description=description)
    db.session.add(job)
    db.session.commit()
    flash('Job added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('home'))
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route("/jobboard")
def jobboard():
    return render_template("jobboard.html")


@app.route("/contact", methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        message = request.form.get('message')
        if not message:
            flash('Message is required', 'danger')
            return redirect(url_for('contact'))
        
        contact = Contact(
            name=current_user.username,
            email=current_user.email,
            message=message
        )
        db.session.add(contact)
        db.session.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    
    return render_template("contact.html")

@app.route("/itjobs")
def itjobs():
    jobs = Job.query.all()
    return render_template("itjobs.html", jobs=jobs)


@app.route("/it1")
def it1():
    return render_template("it1.html")

@app.route("/it2")
def it2():
    return render_template("it2.html")


@app.route("/sales")
def sales():
    return render_template("sales.html") 


@app.route("/sales1")
def sales1():
    return render_template("sales1.html")



@app.route("/sales2")
def sales2():
    return render_template("sales2.html")


@app.route("/marketing")
def marketing():
    return render_template("marketing.html")


@app.route("/marketing1")
def marketing1():
    return render_template("marketing1.html")

@app.route("/marketing2")
def marketing2():
    return render_template("marketing2.html")

@app.route("/data")
def data():
    return render_template("data.html")

@app.route("/data1")
def data1():
    return render_template("data1.html")

@app.route("/data2")
def data2():
    return render_template("data2.html")


@app.route("/hr")
def hr():
    return render_template("hr.html")

@app.route("/hr1")
def hr1():
    return render_template("hr1.html") 

@app.route("/hr2")
def hr2():
    return render_template("hr2.html") 

@app.route("/engineering")
def engineering():
    return render_template("engineering.html")

@app.route("/engineering1")
def engineering1():
    return render_template("engineering1.html")

@app.route("/engineering2")
def engineering2():
    return render_template("engineering2.html")


# jobs by demands
@app.route("/fresher")
def fresher():
    return render_template("fresher.html")

@app.route("/fresher1")
def fresher1():
    return render_template("fresher1.html")


@app.route("/fresher2")
def fresher2():
    return render_template("fresher2.html")

@app.route("/mnc")
def mnc():
    return render_template("mnc.html") 

@app.route("/mnc1")
def mnc1():
    return render_template("mnc1.html") 

@app.route("/mnc2")
def mnc2():
    return render_template("mnc2.html") 


@app.route("/remote")
def remote():
    return render_template("remote.html") 


@app.route("/remote1")
def remote1():
    return render_template("remote1.html") 


@app.route("/remote2")
def remote2():
    return render_template("remote2.html") 

@app.route("/work from home")
def work():
    return render_template("work.html") 

@app.route("/work from home")
def work1():
    return render_template("work1.html") 

@app.route("/work from home")
def work2():
    return render_template("work2.html")


@app.route("/walk")
def walk():
    return render_template("walk.html")


@app.route("/walk")
def walk1():
    return render_template("walk1.html")

@app.route("/walk")
def walk2():
    return render_template("walk2.html")

@app.route("/part")
def part():
    return render_template("part.html")

@app.route("/part1")
def part1():
    return render_template("part1.html")

@app.route("/part2")
def part2():
    return render_template("part2.html")

@app.route("/delhi")
def delhi():
    return render_template("delhi.html")

@app.route("/mumbai")
def mumbai():
    return render_template("mumbai.html") 

@app.route("/banglore") 
def banglore():
    return render_template("banglore.html")

@app.route("/hyderabad")
def hyderabad():
    return render_template("hyderabad.html") 

@app.route("/chennai") 
def chennai():
    return render_template("chennai.html") 

@app.route("/pune")
def pune():
    return render_template("pune.html")

@app.route("/tesla") 
def tesla():
    return render_template("tesla.html")

@app.route("/meta") 
def meta():
    return render_template("meta.html") 

@app.route("/list")
def list():
    return render_template("list.html")

@app.route('/about')
def about():
    return render_template('about.html')

def create_default_jobs():
    # Check if there are any jobs in the database
    if Job.query.count() == 0:
        default_jobs = [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Solutions Inc.",
                "experience": "5-8 years",
                "salary": "₹15-25 LPA",
                "location": "Bangalore",
                "department": "Engineering",
                "company_type": "Product",
                "work_mode": "Hybrid",
                "description": "Looking for a Senior Software Engineer with strong experience in Python, Flask, and React. Must have experience in building scalable web applications."
            },
            {
                "title": "Data Scientist",
                "company": "Analytics Pro",
                "experience": "3-6 years",
                "salary": "₹12-20 LPA",
                "location": "Mumbai",
                "department": "Data Science",
                "company_type": "Service",
                "work_mode": "Remote",
                "description": "Seeking a Data Scientist with expertise in machine learning, Python, and data analysis. Experience with NLP and deep learning is a plus."
            },
            {
                "title": "Product Manager",
                "company": "Innovate Tech",
                "experience": "4-7 years",
                "salary": "₹18-30 LPA",
                "location": "Delhi",
                "department": "Product",
                "company_type": "Product",
                "work_mode": "On-site",
                "description": "Looking for a Product Manager to lead our product development team. Experience in agile methodologies and product strategy required."
            },
            {
                "title": "DevOps Engineer",
                "company": "Cloud Systems",
                "experience": "3-5 years",
                "salary": "₹14-22 LPA",
                "location": "Hyderabad",
                "department": "DevOps",
                "company_type": "Service",
                "work_mode": "Hybrid",
                "description": "DevOps Engineer needed with experience in AWS, Docker, Kubernetes, and CI/CD pipelines. Strong automation skills required."
            },
            {
                "title": "UI/UX Designer",
                "company": "Design Hub",
                "experience": "2-4 years",
                "salary": "₹8-15 LPA",
                "location": "Pune",
                "department": "Design",
                "company_type": "Product",
                "work_mode": "Remote",
                "description": "Seeking a creative UI/UX Designer with experience in Figma, Adobe XD, and user research. Portfolio required."
            }
        ]

        for job_data in default_jobs:
            job = Job(**job_data)
            db.session.add(job)
        
        db.session.commit()
        print("Default jobs added successfully!")

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        experience = request.form.get('experience')
        cover_letter = request.form.get('cover_letter')
        if not cover_letter:
            flash('Cover letter is required', 'danger')
            return redirect(url_for('apply_job', job_id=job_id))
        
        # Check if user has already applied
        existing_application = JobApplication.query.filter_by(
            user_id=current_user.id,
            job_id=job_id
        ).first()
        
        if existing_application:
            flash('You have already applied for this job', 'warning')
            return redirect(url_for('itjobs'))
        
        application = JobApplication(
            user_id=current_user.id,
            job_id=job_id,
            gender=gender,
            dob=dob,
            experience=experience,
            cover_letter=cover_letter
        )
        
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('itjobs'))
    
    return render_template('apply_job.html', job=job, today=date.today().isoformat())

@app.route('/admin/applications')
@login_required
def view_applications():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('home'))
    
    applications = JobApplication.query.order_by(JobApplication.date_applied.desc()).all()
    return render_template('admin.html', applications=applications)

@app.route('/admin/update-application/<int:app_id>', methods=['POST'])
@login_required
def update_application(app_id):
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('home'))
    
    application = JobApplication.query.get_or_404(app_id)
    new_status = request.form.get('status')
    
    if new_status in ['Pending', 'Accepted', 'Rejected']:
        application.status = new_status
        db.session.commit()
        flash('Application status updated successfully!', 'success')
    
    return redirect(url_for('view_applications'))

@app.route('/api/contact-us', methods=['POST'])
def api_contact_us():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    if not name or not email or not message:
        return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400

    contact = Contact(
        name=name,
        email=email,
        message=message
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Message sent successfully!'}), 200

@app.route('/admin-dashboard/')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'danger')
        return redirect(url_for('home'))
    
    jobs = Job.query.all()
    contacts = Contact.query.order_by(Contact.date_submitted.desc()).all()
    applications = JobApplication.query.order_by(JobApplication.date_applied.desc()).all()
    return render_template('admin.html', jobs=jobs, contacts=contacts, applications=applications)

@app.route('/api/contact-messages', methods=['GET'])
def api_contact_messages():
    try:
        app.logger.info('Fetching contact messages')
        contacts = Contact.query.order_by(Contact.date_submitted.desc()).all()
        app.logger.info(f'Found {len(contacts)} contact messages')
        return jsonify([{
            'id': contact.id,
            'name': contact.name,
            'email': contact.email,
            'message': contact.message,
            'date_submitted': contact.date_submitted.strftime('%Y-%m-%d %H:%M:%S')
        } for contact in contacts])
    except Exception as e:
        app.logger.error(f'Error fetching contact messages: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/job-applications', methods=['GET'])
def api_job_applications():
    try:
        app.logger.info('Fetching job applications')
        applications = JobApplication.query.order_by(JobApplication.date_applied.desc()).all()
        app.logger.info(f'Found {len(applications)} job applications')
        return jsonify([{
            'id': app.id,
            'user_id': app.user_id,
            'job_id': app.job_id,
            'cover_letter': app.cover_letter,
            'status': app.status,
            'date_applied': app.date_applied.strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'username': app.user.username,
                'email': app.user.email,
                'mobile': app.user.mobile
            } if app.user else None,
            'job': {
                'title': app.job.title,
                'company': app.job.company
            } if app.job else None
        } for app in applications])
    except Exception as e:
        app.logger.error(f'Error fetching job applications: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-application-status/<int:application_id>', methods=['POST'])
@login_required
def api_update_application_status(application_id):
    try:
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        new_status = data.get('status')
        if not new_status:
            return jsonify({'error': 'Status is required'}), 400
        
        application = JobApplication.query.get_or_404(application_id)
        application.status = new_status
        db.session.commit()
        
        return jsonify({
            'id': application.id,
            'status': application.status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_default_jobs()
    app.run(debug=True, port=5000)