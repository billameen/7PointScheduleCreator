
fetch('./tasks.json')
  .then(r => r.json())
  .then(tasks => {

    const template = document.getElementById("task-item-template");


    console.log("starting loop")

    for ( const [time, task_list] of Object.entries(tasks)) {
        const time_node = document.getElementById(time);

        for (const task of task_list) {
            let template_clone = template.content.cloneNode(true)

            console.log("room num: " + task.room)
            console.log("type:", task.type);
            console.log("selector:", `.${task.type}>.task-items`);

            template_clone.querySelector(".room-number").textContent = task.room;
            if ( task.more_info != null ) template_clone.querySelector(".setup-desc").textContent = `- ${task.more_info}`;

            const task_list_node = time_node.querySelector(`.${task.type}>.task-items`);
            if (task_list_node == null) console.log("task_list_node is null");
            task_list_node.appendChild(template_clone)

        }

    }

});

