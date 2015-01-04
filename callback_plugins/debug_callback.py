import ipdb
import os


class CallbackModule(object):
    def playbook_on_start(self):
        if not os.environ.get('ANSIBLE_STOP_ON_DEBUG', False):
            self.disabled = True

    def playbook_on_task_start(self, name, is_handler):
        if 'debug' in self.task.tags:
            ipdb.set_trace()
