# -*- encoding: utf-8 -*-
from functools import partial
import json
from os import path

LOG_PATH = path.join(
    path.dirname(path.realpath(__file__)),
    'play_log.json')


def stats_to_dict(aggregate_stats):
    data = {
        'aggregated': {
            'changed': aggregate_stats.changed,
            'failures': aggregate_stats.failures,
            'ok': aggregate_stats.ok,
            'skipped': aggregate_stats.skipped,
        },
        'hosts': {
            host: aggregate_stats.summarize(host)
            for host in aggregate_stats.processed
        }
    }
    return data


class CallbackModule(object):
    """
    Logs playbook results as a stream of JSON
    """

    log_methods_args = {
        'runner_on_ok': {'args': ('host', 'result')},
        'runner_on_failed': {'args': ('host', 'result')},
        'runner_on_error': {'args': ('host', 'result')},
        'runner_on_skipped': {'args': ('host', 'item')},
        'runner_on_unreachable': {'args': ('host', 'result')},
        'runner_on_no_hosts': {},
        'runner_on_async_poll': {
            'args': ('host', 'result', 'job_id', 'clock')},
        'runner_on_async_ok': {'args': ('host', 'result', 'job_id')},
        'runner_on_async_failed': {'args': ('host', 'result', 'job_id')},

        'playbook_on_start': {},
        'playbook_on_notify': {'args': ('host', 'handler')},
        'playbook_on_no_hosts_matched': {},
        'playbook_on_no_hosts_remaining': {},
        'playbook_on_task_start': {'args': ('task_name', 'is_handler')},
        'playbook_on_setup': {},
        'playbook_on_import_for_host': {'args': ('host', 'file')},
        'playbook_on_not_import_for_host': {'args': ('host', 'file')},

        'playbook_on_play_start': {'args': ('hosts_pattern',)},
        'playbook_on_stats': {'args': ('stats',)}
    }

    log_methods_args_processors = {
        'stats': stats_to_dict
    }

    def __getattribute__(self, name):
        log_methods_args = object.__getattribute__(self, 'log_methods_args')
        if name in log_methods_args:
            return partial(self._log_and_run_method, name)
        return object.__getattribute__(self, name)

    def _create_log_file(self):
        log_file = open(LOG_PATH, 'w')
        log_file.write('var event_stream = {"stream": [\n')
        return log_file

    def _end_log(self):
        self.log_file.write('{}]};\n')
        self.log_file.close()

    @property
    def log_file(self):
        try:
            return self._log_file
        except AttributeError:
            self._log_file = f = self._create_log_file()
            return f

    def _log_and_run_method(self, method_name, *args, **kwargs):
        self._log_method(method_name, *args, **kwargs)
        try:
            method = object.__getattribute__(self, method_name)
        except AttributeError:
            pass
        else:
            method(*args, **kwargs)

    def playbook_on_stats(self, stats):
        self._end_log()

    def _log_method(self, method_name, *args, **kwargs):
        data = kwargs
        args_names = self.log_methods_args[method_name].get('args', [])
        assert len(args) <= len(args_names)
        data.update(zip(args_names, args))
        for k in data:
            try:
                processor = self.log_methods_args_processors[k]
            except KeyError:
                pass
            else:
                data[k] = processor(data[k])

        data['event_name'] = method_name
        task = getattr(self, 'task', None)
        if task is not None:
            data['task'] = {
                'name': task.name,
                'action': task.action,
                'is_async': task.async_seconds != 0
            }
        self._log(data)

    def _log(self, data):
        json_data = json.dumps(data)
        assert '\n' not in json_data
        self.log_file.write('{},\n'.format(json_data))
