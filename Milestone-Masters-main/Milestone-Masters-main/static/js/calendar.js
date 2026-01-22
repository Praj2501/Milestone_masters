
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the calendar if it exists on the page
    const calendarContainer = document.getElementById('calendar');
    if (calendarContainer) {
        initializeCalendar(calendarContainer);
    }
});

async function fetchTasks() {
    try {
        const response = await fetch('/api/tasks');
        if (!response.ok) {
            throw new Error('Failed to fetch tasks');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching tasks:', error);
        return [];
    }
}

async function initializeCalendar(container) {
    // Get the current date
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();

    // Get all tasks from API
    const tasks = await fetchTasks();

    // Render calendar
    renderCalendar(container, currentYear, currentMonth, tasks);

    // Add event listeners for previous and next month buttons after they're created
    setTimeout(() => {
        const prevBtn = document.getElementById('prev-month');
        const nextBtn = document.getElementById('next-month');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', async function() {
                let newMonth = currentMonth - 1;
                let newYear = currentYear;
                if (newMonth < 0) {
                    newMonth = 11;
                    newYear--;
                }
                renderCalendar(container, newYear, newMonth, tasks);
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', async function() {
                let newMonth = currentMonth + 1;
                let newYear = currentYear;
                if (newMonth > 11) {
                    newMonth = 0;
                    newYear++;
                }
                renderCalendar(container, newYear, newMonth, tasks);
            });
        }
    }, 100);
}

function renderCalendar(container, year, month, tasks) {
    // Clear container
    container.innerHTML = '';

    // Month names
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June', 
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    // Day names
    const dayNames = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

    // Create calendar header with navigation
    const calendarHeader = document.createElement('div');
    calendarHeader.className = 'calendar-header';
    calendarHeader.innerHTML = `
        <div class="month-nav">
            <button id="prev-month" class="btn btn-sm btn-outline-secondary"><i data-feather="chevron-left"></i></button>
            <h3>${monthNames[month]} ${year}</h3>
            <button id="next-month" class="btn btn-sm btn-outline-secondary"><i data-feather="chevron-right"></i></button>
        </div>
        <div class="view-options">
            <button class="today-btn btn btn-sm btn-primary" onclick="window.location.href='/tasks/date/${new Date().toISOString().split('T')[0]}'">Today</button>
        </div>
    `;
    container.appendChild(calendarHeader);

    // Create days header row
    const daysHeader = document.createElement('div');
    daysHeader.className = 'calendar-days-header';
    
    // Add day name headers
    dayNames.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-name';
        dayHeader.textContent = day;
        daysHeader.appendChild(dayHeader);
    });
    
    container.appendChild(daysHeader);

    // Create the grid for the days
    const calendarGrid = document.createElement('div');
    calendarGrid.className = 'calendar-grid';
    
    // Calculate first day of month and total days in month
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    // Get current date for highlighting today
    const now = new Date();
    const currentDate = now.getDate();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'calendar-day empty';
        calendarGrid.appendChild(emptyDay);
    }
    
    // Add cells for days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        dayCell.textContent = day;
        
        // Format date string to match task date format (YYYY-MM-DD)
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        
        // Find tasks for this day
        const dayTasks = tasks.filter(task => task.date === dateStr);
        
        // Add classes based on task status
        if (dayTasks.length > 0) {
            dayCell.classList.add('has-task');
            
            // Check if all tasks for the day are completed
            const allCompleted = dayTasks.every(task => task.completed);
            const anyCompleted = dayTasks.some(task => task.completed);
            
            if (allCompleted) {
                dayCell.classList.add('completed');
            } else if (dateStr < now.toISOString().split('T')[0] && !allCompleted) {
                // Past date with uncompleted tasks
                dayCell.classList.add('missed');
            } else if (anyCompleted) {
                // Partially completed
                dayCell.classList.add('partial');
            }
        }
        
        // Highlight today
        if (day === currentDate && month === currentMonth && year === currentYear) {
            dayCell.classList.add('today');
        }
        
        // Make the day clickable to see tasks
        dayCell.addEventListener('click', function() {
            window.location.href = `/tasks/date/${dateStr}`;
        });
        
        calendarGrid.appendChild(dayCell);
    }
    
    container.appendChild(calendarGrid);
    
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}
