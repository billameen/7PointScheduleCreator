
async function loadTasks() {
    try {
        const response = await fetch('./tasks.json');
        const tasks = await response.json();

        const scheduleBody = document.getElementById('schedule-body');
        const timeSlotTemplate = document.getElementById('time-slot-template');
        const taskItemTemplate = document.getElementById('task-item-template');

        // Create time slots first
        for (const [timeLabel, taskList] of Object.entries(tasks)) {
            // Clone time slot template
            const timeSlot = timeSlotTemplate.content.cloneNode(true);
            const timeRow = timeSlot.querySelector('.time-row');
            timeRow.id = timeLabel;

            // Set time cell text
            timeSlot.querySelector('.time-cell').textContent = timeLabel;

            // Populate tasks for this time slot
            taskList.forEach(task => {
                const taskClone = taskItemTemplate.content.cloneNode(true);

                // Room number
                taskClone.querySelector('.room-number').textContent = task.room;

                // Setup description (more_info)
                if (task.more_info) {
                    taskClone.querySelector('.setup-desc').textContent = `- ${task.more_info}`;
                } else {
                    taskClone.querySelector('.setup-desc').remove();
                }

                // Append to correct task cell based on type
                const taskCell = timeRow.querySelector(`.${task.type} .task-items`);
                if (taskCell) {
                    taskCell.appendChild(taskClone);
                } else {
                    // Fallback to 'other' if type is unknown
                    const otherCell = timeRow.querySelector('.other .task-items');
                    if (otherCell) otherCell.appendChild(taskClone);
                }
            });

            // Append populated time slot to schedule
            scheduleBody.appendChild(timeSlot);
        }

        highlightCurrentTime();
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function highlightCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes() < 30 ? "00" : "30";
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'

    const timeId = `${hours}:${minutes} ${ampm}`;
    const currentRow = document.getElementById(timeId);

    if (currentRow) {
        currentRow.classList.add('current-time');
        currentRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', loadTasks);
