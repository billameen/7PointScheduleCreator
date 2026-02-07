
fetch('./tasks.json')
  .then(r => r.json())
  .then(tasks => {

    const template = document.getElementById("task-item-template");


    for ( const [time, task_list] of Object.entries(tasks)) {
        const time_node = document.getElementById(time);

        for (const task of task_list) {
            let template_clone = template.content.cloneNode(true)

            template_clone.querySelector(".room-number").textContent = task.room;
            if ( task.more_info != null ) template_clone.querySelector(".setup-desc").textContent = `- ${task.more_info}`;

            const task_list_node = time_node.querySelector(`.${task.type}>.task-items`);
            task_list_node.appendChild(template_clone)

        }

    }

});

