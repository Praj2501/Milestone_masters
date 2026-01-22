document.addEventListener('DOMContentLoaded', function() {
    // Initialize our custom calendar
    if (document.getElementById('task-calendar')) {
        // Calendar initialization is handled in calendar.js
    }

    // Initialize FullCalendar (if still needed for other views)
    if (document.getElementById('calendar')) {
        const calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            events: '/api/events',
            eventClick: function(info) {
                showTaskDetails(info.event);
            }
        });
        calendar.render();
    }

    // Task completion handling - only allow today's tasks to be completed
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.task-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            // Check if the task is for today
            const taskDate = this.dataset.taskDate;
            const today = new Date().toISOString().split('T')[0]; // Format: YYYY-MM-DD

            if (taskDate !== today) {
                alert('You can only complete tasks for today!');
                this.checked = false;
                return;
            }

            if (this.checked) {
                const taskId = this.dataset.taskId;
                try {
                    // Disable the checkbox while validation is in progress
                    this.disabled = true;

                    const response = await openConceptValidation(taskId);

                    if (!response) {
                        this.checked = false;
                        this.disabled = false;
                    } else {
                        // If validation is successful, keep it checked and disabled
                        this.checked = true;
                        this.disabled = true;

                        // Update the label text
                        const label = this.closest('.form-check').querySelector('.form-check-label');
                        if (label) {
                            label.innerHTML = '<span class="task-badge badge-success">Completed</span>';
                        }
                    }
                } catch (error) {
                    console.error('Error validating task:', error);
                    this.checked = false;
                    this.disabled = false;
                    alert('There was an error validating your task. Please try again.');
                }
            }
        });
    });
});

    // Concept validation modal
    async function openConceptValidation(taskId) {
        const response = await Swal.fire({
            title: 'Concept Validation',
            text: 'Please explain what you learned from this task:',
            input: 'textarea',
            showCancelButton: true,
            confirmButtonText: 'Submit',
            cancelButtonText: 'Cancel',
            preConfirm: async (response) => {
                try {
                    const result = await fetch(`/validate_concept/${taskId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ response: response })
                    });
                    return await result.json();
                } catch (error) {
                    Swal.showValidationMessage(`Request failed: ${error}`);
                }
            }
        });

        if (response.isConfirmed && response.value.success) {
            Swal.fire('Success!', 'Concept validated successfully!', 'success');
            return true;
        } else if (response.isConfirmed) {
            Swal.fire('Try Again', 'Please review the concept and try again', 'error');
            return false;
        }
        return false;
    }

    // Goal form date validation
    const startDate = document.getElementById('start_date');
    const endDate = document.getElementById('end_date');

    if (startDate && endDate) {
        startDate.addEventListener('change', function() {
            endDate.min = this.value;
        });

        endDate.addEventListener('change', function() {
            startDate.max = this.value;
        });
    }

    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('active');
        });
    }

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});
// Task validation function
async function openConceptValidation(taskId) {
    const currentTaskId = taskId;

    // Get task description
    try {
        const response = await fetch(`/api/tasks`);
        const tasks = await response.json();
        const task = tasks.find(t => t.id == taskId);

        if (!task) {
            console.error('Task not found');
            return false;
        }
    } catch (error) {
        console.error("Error fetching task data:", error);
        return false;
    }

    // Find or create validation modal
    let validationModal = bootstrap.Modal.getInstance(document.getElementById('conceptValidationModal'));

    if (!validationModal) {
        // If we're on the day_tasks page, we need to create the modal
        const modalHTML = `
        <div class="modal fade" id="conceptValidationModal" tabindex="-1" aria-labelledby="conceptValidationModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="conceptValidationModalLabel">Validate Your Learning</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="task-details mb-3">
                            <h6>Today's Task:</h6>
                            <p id="taskDescription" class="mb-3"></p>
                        </div>
                        <div class="chat-container mb-3" id="validationChat">
                            <div class="bot-message chat-message">
                                Please explain what you learned from this task. Be specific about:
                                1. The concepts you understood
                                2. How you would apply them
                                3. Any challenges you faced
                            </div>
                        </div>
                        <div class="input-group">
                            <textarea class="form-control" id="conceptResponse" 
                                    rows="3" placeholder="Type your explanation here..."></textarea>
                            <button class="btn btn-primary d-flex align-items-center" id="sendConceptResponse">
                                <i data-feather="send" class="me-2"></i> Send
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

        // Append modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        validationModal = new bootstrap.Modal(document.getElementById('conceptValidationModal'));

        // Setup send button event
        document.getElementById('sendConceptResponse').addEventListener('click', async function() {
            await submitConceptResponse(currentTaskId);
        });
    }

    // Set task description and show modal
    document.getElementById('taskDescription').textContent = task.description;
    validationModal.show();

    return true;
}

// Function to submit concept validation response
async function submitConceptResponse(taskId) {
    const responseText = document.getElementById('conceptResponse').value.trim();

    if (!responseText) {
        alert('Please enter your response');
        return;
    }

    try {
        const response = await fetch(`/validate_concept/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ response: responseText })
        });

        const result = await response.json();
        const validationChat = document.getElementById('validationChat');

        // Add user's message to chat
        validationChat.innerHTML += `
            <div class="user-message chat-message">
                ${responseText.replace(/\n/g, '<br>')}
            </div>
        `;

        // Add bot's response
        validationChat.innerHTML += `
            <div class="bot-message chat-message">
                ${result.feedback.replace(/\n/g, '<br>')}
            </div>
        `;

        // Clear input
        document.getElementById('conceptResponse').value = '';

        // If successful, refresh page after a delay
        if (result.success) {
            setTimeout(() => {
                location.reload();
            }, 3000);
        }
    } catch (error) {
        console.error('Error submitting response:', error);
        alert('An error occurred. Please try again.');
    }
}

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Task completion handling on day_tasks page
    document.querySelectorAll('.task-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', async function() {
            if (this.checked) {
                const taskId = this.dataset.taskId;
                const success = await openConceptValidation(taskId);
                if (!success) {
                    this.checked = false;
                }
            }
        });
    });

    // Add other initialization code here
});