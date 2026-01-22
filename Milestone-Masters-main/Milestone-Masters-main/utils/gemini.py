import os
import logging
from datetime import datetime, timedelta
import google.generativeai as genai

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key not found in environment variables")
    genai.configure(api_key=api_key)
    # Use the correct model name from available models
    return genai.GenerativeModel('gemini-1.5-pro')

def generate_topic_list(goal_title, days_count):
    """Generate a list of relevant topics based on the goal title"""
    # Default topics for common programming languages/subjects
    default_topics = {
        "python": [
            "Basic syntax", "Variables and data types", "Control flow", 
            "Functions", "Data structures", "File handling", 
            "Error handling", "Object-oriented programming", "Modules and packages",
            "Advanced functions", "Working with APIs", "Testing", "Web frameworks",
            "List comprehensions", "Decorators", "Generators and iterators", 
            "Context managers", "Lambda expressions", "Regular expressions",
            "Python for data analysis", "Python for automation", "Multithreading", 
            "Multiprocessing", "Async programming", "Working with databases",
            "Web scraping", "Python socket programming", "Building CLI applications", 
            "GUI development with Tkinter", "Python with cloud services", "Pandas",
            "NumPy", "Matplotlib", "Scikit-learn", "Django", "Flask", "FastAPI"
        ],
        "javascript": [
            "Basic syntax", "Variables and data types", "Control flow", 
            "Functions", "Arrays and objects", "DOM manipulation", 
            "Events", "Asynchronous JS", "Error handling", "ES6 features",
            "Modules", "Frameworks introduction", "API integration"
        ],
        "web development": [
            "HTML basics", "CSS fundamentals", "Layout techniques", 
            "Responsive design", "JavaScript basics", "DOM manipulation", 
            "Forms and validation", "API integration", "Frontend frameworks intro",
            "Backend basics", "Databases", "Authentication", "Deployment"
        ],
        "machine learning": [
            "Data preparation", "Basic statistics", "Linear regression", 
            "Classification algorithms", "Model evaluation", "Feature engineering", 
            "Decision trees", "Neural networks intro", "Python ML libraries",
            "Model optimization", "Clustering", "Natural language processing", "Computer vision"
        ]
    }
    
    # Convert goal title to lowercase for matching
    goal_lower = goal_title.lower()
    
    # Find matching topics or create generic ones
    for key in default_topics:
        if key in goal_lower:
            topics = default_topics[key][:days_count]
            # If we need more topics than we have in our default list
            while len(topics) < days_count:
                topics.append(f"Advanced {key} topic {len(topics) - len(default_topics[key]) + 1}")
            return topics
    
    # Generic topics if no match found
    return [f"{goal_title} - Topic {i+1}" for i in range(days_count)]

    if not api_key:
        raise ValueError("Gemini API key not found in environment variables")
    genai.configure(api_key=api_key)
    # Use the correct model name from available models
    return genai.GenerativeModel('gemini-1.5-pro')

def generate_task_schedule(goal_title, goal_description, start_date, end_date):
    """Generate a schedule using Gemini model"""
    try:
        model = init_gemini()
        # Convert dates to string format if they're date objects
        start_date_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date
        end_date_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else end_date

        days_between = (end_date - start_date).days + 1 if hasattr(start_date, 'strftime') else 1

        prompt = f"""
        Create a focused {days_between}-day learning schedule specifically for learning: {goal_title}
        Description: {goal_description}
        Start Date: {start_date_str}
        End Date: {end_date_str}

        For each day, provide ONLY relevant tasks directly related to {goal_title}.
        
        Each daily task should include:
        1. A specific, concise learning objective for the day
        2. ONE key concept to learn
        3. ONE practical coding exercise that builds real-world skills
        
        Format each task EXACTLY as:
        DATE: YYYY-MM-DD | TASK: Day [X]: [Specific topic] - Objective: [Clear learning goal] - Task: [Key concept] - Practice: [Coding exercise with specific instructions]
        
        Rules:
        1. Keep tasks strictly focused on {goal_title} without adding unrelated content
        2. Tasks should have concrete, achievable coding objectives
        3. Ensure a logical progression from fundamentals to advanced topics
        4. Make exercises practical and applicable to real-world scenarios
        5. For Python specifically, include best practices and idiomatic approaches
        6. Provide specific, actionable instructions rather than vague suggestions
        7. Tasks should build upon previous learning
        8. Advanced topics should include specific libraries, techniques, or applications
        """

        logger.debug(f"Generating schedule with prompt for goal: {goal_title}")
        response = model.generate_content(prompt)
        tasks = []

        for line in response.text.split('\n'):
            if '|' in line:
                try:
                    date_part, task_part = line.split('|')
                    if 'DATE:' in date_part and 'TASK:' in task_part:
                        date_str = date_part.replace('DATE:', '').strip()
                        task_desc = task_part.replace('TASK:', '').strip()
                        task_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        if start_date <= task_date <= end_date:
                            tasks.append((task_date, task_desc))
                except ValueError as e:
                    logger.error(f"Error parsing task line '{line}': {str(e)}")
                    continue

        if not tasks:
            # Fallback: Generate focused daily tasks relevant to the goal title
            topics = generate_topic_list(goal_title, days_between)
            current_date = start_date
            day_count = 1
            
            # Specific learning objectives and exercises for Python topics
            python_objectives = {
                "Basic syntax": "Learn Python's indentation rules, comments, and basic operators",
                "Variables and data types": "Understand different data types (int, float, string, bool) and type conversion",
                "Control flow": "Master if-else statements, loops, and conditional expressions",
                "Functions": "Create and use functions with parameters, return values, and default arguments",
                "Data structures": "Work with lists, dictionaries, tuples, and sets",
                "File handling": "Open, read, write, and close files using different modes",
                "Error handling": "Implement try-except blocks to handle exceptions gracefully",
                "Object-oriented programming": "Create classes, objects, inheritance, and use special methods",
                "Modules and packages": "Import and use modules, create your own modules",
                "Advanced functions": "Explore higher-order functions, closures, and recursion",
                "Working with APIs": "Make HTTP requests and parse JSON responses",
                "Testing": "Write unit tests using pytest or unittest",
                "Web frameworks": "Build a simple web application with Flask",
                "List comprehensions": "Write concise code for creating lists with conditions and transformations",
                "Decorators": "Modify function behavior with decorator functions",
                "Generators and iterators": "Create memory-efficient sequences using generator functions",
                "Context managers": "Implement resource management with context managers",
                "Lambda expressions": "Write anonymous functions for simple operations",
                "Regular expressions": "Parse and validate text using regex patterns",
                "Python for data analysis": "Process data using pandas DataFrames",
                "Python for automation": "Automate tasks with scripts",
                "Multithreading": "Run code concurrently with threads",
                "Multiprocessing": "Execute tasks in parallel using multiple CPU cores",
                "Async programming": "Use async/await for non-blocking code execution",
                "Working with databases": "Connect to SQL databases and execute queries",
                "Web scraping": "Extract data from websites using BeautifulSoup or Scrapy",
                "Python socket programming": "Create client-server applications",
                "Building CLI applications": "Design command-line interfaces with argparse",
                "GUI development with Tkinter": "Build desktop applications with Python's built-in GUI toolkit",
                "Python with cloud services": "Integrate with AWS, Azure, or Google Cloud",
                "Pandas": "Analyze and manipulate tabular data efficiently",
                "NumPy": "Perform numerical computing with arrays",
                "Matplotlib": "Create data visualizations and plots",
                "Scikit-learn": "Build machine learning models with Python",
                "Django": "Develop full-featured web applications",
                "Flask": "Create lightweight web services",
                "FastAPI": "Build high-performance APIs with automatic documentation"
            }
            
            python_exercises = {
                "Basic syntax": "Write a program that prints 'Hello, World!' and calculates simple math expressions",
                "Variables and data types": "Create variables of different types and perform operations on them",
                "Control flow": "Write a program that determines if a number is prime using conditionals and loops",
                "Functions": "Create a function to calculate the factorial of a number",
                "Data structures": "Build a contact list using dictionaries with operations to add, remove, and search",
                "File handling": "Create a program that reads a CSV file, processes data, and writes results to a new file",
                "Error handling": "Write a program that safely divides numbers and handles potential errors",
                "Object-oriented programming": "Design a 'Bank Account' class with methods for deposit, withdrawal, and balance check",
                "Modules and packages": "Create a module with utility functions and import it in a main script",
                "Advanced functions": "Implement a decorator that times how long a function takes to execute",
                "Working with APIs": "Build a weather app that fetches data from a public API",
                "Testing": "Write tests for the 'Bank Account' class created earlier",
                "Web frameworks": "Create a simple Flask application with routes and templates",
                "List comprehensions": "Convert for loops to list comprehensions in various examples",
                "Decorators": "Create a caching decorator for expensive function calls",
                "Generators and iterators": "Implement a custom range function using generators",
                "Context managers": "Create a custom context manager for file handling",
                "Lambda expressions": "Use lambda functions with map, filter, and sort",
                "Regular expressions": "Build an email validator using regex",
                "Python for data analysis": "Clean and analyze a sample dataset",
                "Python for automation": "Create a script that organizes files in a directory by type",
                "Multithreading": "Build a program that downloads multiple files concurrently",
                "Multiprocessing": "Process a large dataset in parallel",
                "Async programming": "Create an async web scraper",
                "Working with databases": "Build a simple contact management system with SQLite",
                "Web scraping": "Extract data from a news website",
                "Python socket programming": "Create a simple chat application",
                "Building CLI applications": "Build a command-line todo list manager",
                "GUI development with Tkinter": "Create a calculator application with GUI",
                "Python with cloud services": "Upload files to S3 or similar service",
                "Pandas": "Analyze and visualize real-world dataset",
                "NumPy": "Solve mathematical problems using NumPy arrays",
                "Matplotlib": "Create various charts and plots from sample data",
                "Scikit-learn": "Build and evaluate a simple classification model",
                "Django": "Create a blog application with user authentication",
                "Flask": "Build a RESTful API",
                "FastAPI": "Develop a high-performance API with validation"
            }
            
            while current_date <= end_date and day_count <= len(topics):
                topic = topics[day_count-1] if day_count <= len(topics) else f"Advanced {goal_title} concepts"
                
                # Get specific objective and exercise for the topic, or use generic ones
                objective = python_objectives.get(topic, f"Learn the fundamentals of {topic}")
                exercise = python_exercises.get(topic, f"Create a simple example demonstrating {topic}")
                
                task_desc = (
                    f"Day {day_count}: {topic}\n"
                    f"Objective: {objective}\n"
                    f"Task: Apply {topic} concepts in Python code\n"
                    f"Practice: {exercise}"
                )
                tasks.append((current_date, task_desc))
                current_date += timedelta(days=1)
                day_count += 1

        logger.info(f"Generated {len(tasks)} tasks for goal: {goal_title}")
        return sorted(tasks, key=lambda x: x[0])

    except Exception as e:
        logger.error(f"Error generating schedule: {str(e)}")
        return []

def validate_learning(task_description, user_response):
    try:
        model = init_gemini()
        prompt = f"""
        Validate the learning response:
        Task: {task_description}
        User's Response: {user_response}

        Evaluation Criteria:
        1. Direct relevance to the specific task
        2. Understanding of the specific concept
        3. Evidence of completing the practice activity
        4. Conciseness and clarity

        Return EXACTLY in this format:
        VALID: [Yes/No]
        FEEDBACK: [Brief, specific feedback focused only on the task at hand, with 1-2 improvement suggestions if needed]
        """

        response = model.generate_content(prompt)
        text = response.text

        is_valid = "VALID: Yes" in text
        feedback = text.split("FEEDBACK:")[1].strip() if "FEEDBACK:" in text else text

        return is_valid, feedback

    except Exception as e:
        logger.error(f"Error validating learning: {str(e)}")
        return False, f"Error validating response: {str(e)}"

def chat_with_gemini(message, context=None):
    try:
        model = init_gemini()
        base_prompt = """You are an AI learning assistant helping users understand concepts 
        and achieve their learning goals. Your responses should be:
        1. Clear and concise
        2. Include practical examples
        3. Break down complex concepts
        4. Encourage active learning
        5. Validate understanding through questions

        Always maintain a supportive and encouraging tone."""

        if context:
            prompt = f"{base_prompt}\nPrevious context: {context}\nUser: {message}"
        else:
            prompt = f"{base_prompt}\nUser: {message}"

        response = model.generate_content(prompt)
        return {
            'success': True,
            'response': response.text,
            'error': None
        }
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return {
            'success': False,
            'response': None,
            'error': str(e)
        }