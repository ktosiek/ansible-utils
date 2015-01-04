function Playbook(plays) {
    this.plays = plays;
}

function Play(hosts, tasks) {
    this.hosts_pattern = hosts;
    this.tasks = tasks;
}

function Task(task, result) {
    this.task = task;
    this.result = result;
}

Task.from_data = function (data) {
    return new Task(data.task, data.result);
}

function EventsParser() {
    var self = this, current_play_data, current_task_data;

    self.plays = [];

    function finish_current_task() {
        if (current_task_data) {
            current_play_data.tasks.push(Task.from_data(current_task_data));
        };
        current_task_data = undefined;
    }

    function finish_current_play() {
        if (current_play_data) {
            self.plays.push(
                new Play(current_play_data.hosts,
                         current_play_data.tasks));
        }
        current_play_data = undefined;
    }


    self.fsm = new machina.Fsm({
        initialState: "before_play",

        states: {
            "before_play": {
                "playbook_on_play_start": function (data) {
                    finish_current_play();

                    current_play_data = {tasks: []};
                    current_play_data.hosts = data.hosts_pattern;
                },

                "playbook_on_stats": function (data) {
                    finish_current_play();
                },

                "playbook_on_task_start": function () {
                    this.deferUntilTransition();
                    this.transition("task");
                }
            },

            "task": {
                "playbook_on_task_start": function (data) {
                    finish_current_task();

                    current_task_data = data;

                    if (data.task.is_async) {
                        this.transition("task_async");
                    }
                },

                "runner_on_ok": function (data) {
                    $.extend(current_task_data, data, {'result': 'ok'});
                },
                "runner_on_failed": function (data) {
                    $.extend(current_task_data, data, {'result': 'failed'});
                },
                "runner_on_error": function (data) {
                    $.extend(current_task_data, data, {'result': 'error'});
                },
                "runner_on_skipped": function (data) {
                    $.extend(current_task_data, data, {'result': 'skipped'});
                },

                "playbook_on_stats": function () {
                    finish_current_task();

                    this.deferUntilTransition();
                    this.transition("before_play");
                },

                "playbook_on_play_start": function () {
                    finish_current_task();

                    this.deferUntilTransition();
                    this.transition("before_play");
                }
            },
            "task_async": {
                _onEnter: function () {
                    current_task_data.is_async = true;
                    current_task_data.async_polls = [];
                },

                "runner_on_async_poll": function (data) {
                    current_task_data.async_polls.push(data);
                },

                "runner_on_async_ok": function (data) {
                    this.transition("task");
                    this.handle("runner_on_ok", data);
                },
                "runner_on_async_failed": function (data) {
                    this.transition("task");
                    this.handle("runner_on_failed", data);
                }
            },
        }
    });
}

EventsParser.prototype.push_event = function (event) {
    console.log(event.event_name, event);
    this.fsm.handle(event.event_name, event);
}

EventsParser.prototype.get_playbook = function () {
    return new Playbook(this.plays);
}
