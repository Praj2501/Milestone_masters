import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import google.generativeai as genai
from sqlalchemy.orm import DeclarativeBase
from utils.gemini import chat_with_gemini, validate_learning, generate_task_schedule
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///goals.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Gemini AI configuration
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

from models import User, Goal, Task
from forms import GoalForm

# Add nl2br template filter
@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ""
    return s.replace('\n', '<br>')

@app.route('/')
def dashboard():
    goals = Goal.query.all()
    stats = calculate_stats()
    today_date = datetime.now().date().strftime('%Y-%m-%d')
    return render_template('dashboard.html', goals=goals, stats=stats, today_date=today_date)

@app.route('/goal/new', methods=['GET', 'POST'])
def new_goal():
    form = GoalForm()
    if form.validate_on_submit():
        try:
            # Create new goal
            goal = Goal(
                title=form.title.data,
                description=form.description.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                user_id=1  # Default user ID for now
            )
            db.session.add(goal)
            db.session.commit()
            logger.info(f"Created new goal: {goal.title}")

            # Generate schedule using Gemini AI
            tasks = generate_task_schedule(
                goal.title,
                goal.description,
                goal.start_date,
                goal.end_date
            )

            if tasks:
                # Add generated tasks to database
                for task_date, task_desc in tasks:
                    task = Task(
                        date=task_date,
                        description=task_desc,
                        goal_id=goal.id
                    )
                    db.session.add(task)
                db.session.commit()
                logger.info(f"Generated {len(tasks)} tasks for goal: {goal.title}")
                flash('Goal and schedule created successfully!', 'success')
            else:
                logger.warning(f"No tasks generated for goal: {goal.title}")
                flash('Goal created but there was an error generating the schedule.', 'warning')

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating goal: {str(e)}")
            flash('Error creating goal. Please try again.', 'error')

        return redirect(url_for('dashboard'))

    return render_template('goal.html', form=form)

@app.route('/validate_concept/<int:task_id>', methods=['POST'])
def validate_concept(task_id):
    task = Task.query.get_or_404(task_id)
    user_response = request.json.get('response')

    if not user_response:
        return jsonify({'error': 'No response provided'}), 400

    is_valid, feedback = validate_learning(task.description, user_response)

    if is_valid:
        task.completed = True
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving task completion: {str(e)}")
            return jsonify({'error': 'Error saving completion status'}), 500

    return jsonify({
        'success': is_valid,
        'feedback': feedback
    })

@app.route('/task/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.json

    if 'description' not in data:
        return jsonify({'error': 'No description provided'}), 400

    try:
        task.description = data['description']
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating task: {str(e)}")
        return jsonify({'error': str(e)}), 500

def calculate_stats():
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(completed=True).count()
    return {
        "streak": calculate_streak(),
        "active_days": completed_tasks,
        "missing_days": total_tasks - completed_tasks
    }

def calculate_streak():
    tasks = Task.query.filter_by(completed=True).order_by(Task.date.desc()).all()
    streak = 0
    current_date = datetime.now().date()

    for task in tasks:
        if (current_date - task.date).days == streak:
            streak += 1
        else:
            break

    return streak

@app.route('/chat')
def chat():
    return render_template('chat.html')
    
@app.route('/help')
def help_page():
    """Display help information about how to use the app"""
    return render_template('help.html')

@app.route('/chat/send', methods=['POST'])
def process_chat():
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    result = chat_with_gemini(message)

    if result['success']:
        return jsonify({
            'response': result['response']
        })
    else:
        return jsonify({
            'error': result['error'] or 'Failed to process message'
        }), 500

@app.route('/goal/delete/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    goal = Goal.query.get_or_404(goal_id)
    try:
        # Delete associated tasks first
        Task.query.filter_by(goal_id=goal.id).delete()
        # Then delete the goal
        db.session.delete(goal)
        db.session.commit()
        flash('Goal deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting goal. Please try again.', 'error')
        logger.error(f"Error deleting goal: {str(e)}")
    return redirect(url_for('dashboard'))

@app.route('/api/tasks')
def get_tasks():
    """API endpoint to get tasks for calendar view"""
    tasks = Task.query.all()
    task_list = []
    
    for task in tasks:
        task_list.append({
            'id': task.id,
            'date': task.date.strftime('%Y-%m-%d'),
            'description': task.description,
            'completed': task.completed,
            'goal_id': task.goal_id
        })
    
    return jsonify(task_list)

@app.route('/tasks/date/<date_string>')
def tasks_by_date(date_string):
    """Show tasks for a specific date"""
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d').date()
        tasks = Task.query.filter_by(date=date_obj).all()
        
        # Check if the date is today
        is_today = date_obj == datetime.now().date()
        
        # Log for debugging
        logger.debug(f"Date requested: {date_string}, is today: {is_today}")
        logger.debug(f"Tasks found: {len(tasks)}")
        
        return render_template('day_tasks.html', 
                              tasks=tasks, 
                              date=date_obj,
                              is_today=is_today)
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('dashboard'))

with app.app_context():
    db.create_all()
    # Create default user if not exists
    if not User.query.filter_by(id=1).first():
        default_user = User(
            id=1,
            username="default",
            email="default@example.com",
            password_hash="default"
        )
        db.session.add(default_user)
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)