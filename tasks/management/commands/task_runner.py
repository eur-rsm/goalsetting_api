import csv
from datetime import datetime
import os
from pathlib import Path
import time
from typing import List

from background_task.models import Task, TaskManager
from background_task.tasks import tasks, autodiscover
from dateutil import parser
from django.conf import settings
from django.core.management.base import BaseCommand
from pytz import timezone

from chat.conversation import schedule_conversation


class Command(BaseCommand):
    help = 'Run tasks periodically'

    def handle(self, **options):
        self.ensure_conversations()
        self.ensure_one_signal()
        self.task_runner()

    @classmethod
    def task_runner(cls):
        autodiscover()

        while True:
            more_tasks = tasks.run_next_task()
            if more_tasks:
                time.sleep(.1)
            else:
                time.sleep(1)

            cls.crash_on_db_loss()

    @staticmethod
    def crash_on_db_loss():
        # Unfortunately, background tasks can't reconnect if DB conn is lost
        # Look for error in log, crash the process, let cron restart
        with open('./_log/tasks.log', 'rb') as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode().replace('\n', '')

            if last_line == 'Failed to retrieve tasks. Database unreachable.':
                print()
                print('Exiting...')
                print()

                import sys
                sys.exit(1)

    @staticmethod
    def ensure_one_signal():
        from api.notifications import retrieve_onesignal_ids
        retrieve_onesignal_ids(repeat=settings.REPEAT,
                               remove_existing_tasks=True)

    @classmethod
    def ensure_conversations(cls):
        # Get the already scheduled tasks
        all_tasks = Task.objects.all()
        task_tuples = {(task.params()[0][0] if task.params()[0] else '',
                        task.run_at) for task in all_tasks}

        # Get all the needed tasks
        file_path = Path(settings.TASKS_CSV)
        needed_tasks = cls.read_csv(file_path)
        now = datetime.now().replace(tzinfo=timezone('UTC'))

        for needed_task in needed_tasks:
            conversation_name = needed_task[1].strip()
            # Make sure the conversations are triggered via direct intent
            if not conversation_name.startswith('/'):
                conversation_name = f'/{conversation_name}'
            date_time = parser.parse(needed_task[0])
            date_time = date_time.replace(tzinfo=timezone('UTC'))

            # Don't schedule in the past, indicative for faulty input
            if date_time < now:
                continue

            # Don't try to reschedule same task
            if (conversation_name, date_time) in task_tuples:
                continue

            task = TaskManager().new_task(schedule_conversation.name,
                                          args=(conversation_name,),
                                          run_at=date_time,
                                          remove_existing_tasks=False)
            task.save()

    @staticmethod
    def read_csv(file_path: Path) -> List:
        with file_path.open('r') as f:
            reader = csv.reader(f, delimiter=';', quotechar='"')
            # Ignore header
            next(reader)
            for row in reader:
                yield row
