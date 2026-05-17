from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from config import Config
from models import (
    db, User, Class, Enrollment,
    Announcement, Assignment, Submission, Material
)
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ══════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        if role not in ('teacher', 'student'):
            role = 'student'
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'error')
            return redirect(url_for('signup'))
        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created successfully! Welcome to EduClass.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('auth/signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ══════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_teacher():
        classes = Class.query.filter_by(
            teacher_id=current_user.id
        ).order_by(Class.created_at.desc()).all()
    else:
        enrollments = Enrollment.query.filter_by(
            student_id=current_user.id
        ).all()
        classes = [e.enrolled_class for e in enrollments if e.enrolled_class]
    return render_template('shared/dashboard.html', classes=classes)


# ══════════════════════════════════════════
#  CLASSES
# ══════════════════════════════════════════

@app.route('/class/create', methods=['GET', 'POST'])
@login_required
def create_class():
    if not current_user.is_teacher():
        flash('Only teachers can create classes.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        class_name = request.form.get('class_name', '').strip()
        section = request.form.get('section', '').strip()
        subject = request.form.get('subject', '').strip()
        room = request.form.get('room', '').strip()
        theme_color = request.form.get('theme_color', '#7c3aed')
        if not class_name:
            flash('Class name is required.', 'error')
            return render_template('teacher/create_class.html')
        new_class = Class(
            class_name=class_name,
            section=section,
            subject=subject,
            room=room,
            class_code=Class.generate_code(),
            teacher_id=current_user.id,
            theme_color=theme_color
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('teacher/create_class.html')


@app.route('/class/join', methods=['GET', 'POST'])
@login_required
def join_class():
    if not current_user.is_student():
        flash('Only students can join classes.', 'error')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        code = request.form.get('class_code', '').strip().upper()
        cls = Class.query.filter_by(class_code=code).first()
        if not cls:
            flash('Invalid class code. Please try again.', 'error')
            return render_template('student/join_class.html')
        already = Enrollment.query.filter_by(
            class_id=cls.id,
            student_id=current_user.id
        ).first()
        if already:
            flash('You are already enrolled in this class.', 'error')
            return redirect(url_for('dashboard'))
        enrollment = Enrollment(class_id=cls.id, student_id=current_user.id)
        db.session.add(enrollment)
        db.session.commit()
        flash(f'Successfully joined {cls.class_name}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('student/join_class.html')


@app.route('/class/<int:class_id>')
@login_required
def class_stream(class_id):
    cls = Class.query.get_or_404(class_id)
    announcements = Announcement.query.filter_by(
        class_id=class_id
    ).order_by(Announcement.created_at.desc()).all()
    return render_template(
        'shared/class_stream.html',
        cls=cls,
        announcements=announcements
    )


@app.route('/class/<int:class_id>/classwork')
@login_required
def classwork(class_id):
    cls = Class.query.get_or_404(class_id)
    assignments = Assignment.query.filter_by(
        class_id=class_id
    ).order_by(Assignment.created_at.desc()).all()
    materials = Material.query.filter_by(
        class_id=class_id
    ).order_by(Material.created_at.desc()).all()
    return render_template(
        'shared/classwork.html',
        cls=cls,
        assignments=assignments,
        materials=materials
    )


@app.route('/class/<int:class_id>/people')
@login_required
def class_people(class_id):
    cls = Class.query.get_or_404(class_id)
    enrollments = Enrollment.query.filter_by(class_id=class_id).all()
    students = [e.student for e in enrollments if e.student]
    return render_template(
        'shared/people.html',
        cls=cls,
        students=students
    )


# ══════════════════════════════════════════
#  ANNOUNCEMENTS
# ══════════════════════════════════════════

@app.route('/class/<int:class_id>/announce', methods=['POST'])
@login_required
def post_announcement(class_id):
    content = request.form.get('content', '').strip()
    if content:
        ann = Announcement(
            class_id=class_id,
            author_id=current_user.id,
            content=content
        )
        db.session.add(ann)
        db.session.commit()
        flash('Announcement posted!', 'success')
    return redirect(url_for('class_stream', class_id=class_id))


# ══════════════════════════════════════════
#  ASSIGNMENTS
# ══════════════════════════════════════════

@app.route('/class/<int:class_id>/assignment/create', methods=['GET', 'POST'])
@login_required
def create_assignment(class_id):
    if not current_user.is_teacher():
        flash('Only teachers can create assignments.', 'error')
        return redirect(url_for('dashboard'))
    cls = Class.query.get_or_404(class_id)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '')
        total_marks = request.form.get('total_marks', 100)
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass
        assignment = Assignment(
            class_id=class_id,
            teacher_id=current_user.id,
            title=title,
            description=description,
            due_date=due_date,
            total_marks=int(total_marks)
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment created!', 'success')
        return redirect(url_for('classwork', class_id=class_id))
    return render_template('teacher/create_assignment.html', cls=cls)


@app.route('/assignment/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    submission = None
    if current_user.is_student():
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
    return render_template(
        'student/submit_assignment.html',
        assignment=assignment,
        submission=submission
    )


@app.route('/assignment/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    if not current_user.is_student():
        flash('Only students can submit assignments.', 'error')
        return redirect(url_for('dashboard'))
    assignment = Assignment.query.get_or_404(assignment_id)
    existing = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=current_user.id
    ).first()
    if existing:
        flash('You have already submitted this assignment.', 'error')
        return redirect(url_for('classwork', class_id=assignment.class_id))
    comment = request.form.get('comment', '').strip()
    submission = Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        comment=comment,
        status='submitted'
    )
    db.session.add(submission)
    db.session.commit()
    flash('Assignment submitted successfully!', 'success')
    return redirect(url_for('classwork', class_id=assignment.class_id))


@app.route('/assignment/<int:assignment_id>/grade', methods=['GET', 'POST'])
@login_required
def grade_assignment(assignment_id):
    if not current_user.is_teacher():
        flash('Only teachers can grade assignments.', 'error')
        return redirect(url_for('dashboard'))
    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = Submission.query.filter_by(
        assignment_id=assignment_id
    ).all()
    if request.method == 'POST':
        for sub in submissions:
            marks_key = f'marks_{sub.id}'
            feedback_key = f'feedback_{sub.id}'
            marks_val = request.form.get(marks_key, '').strip()
            feedback_val = request.form.get(feedback_key, '').strip()
            if marks_val:
                sub.marks_obtained = int(marks_val)
                sub.feedback = feedback_val
                sub.status = 'graded'
        db.session.commit()
        flash('Grades saved successfully!', 'success')
        return redirect(url_for('classwork', class_id=assignment.class_id))
    return render_template(
        'teacher/grade_assignment.html',
        assignment=assignment,
        submissions=submissions
    )


# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)