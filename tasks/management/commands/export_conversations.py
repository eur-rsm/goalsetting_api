import csv
from datetime import datetime
from typing import List, Tuple
from lxml import etree

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from chat.models import ChatMessage


class Command(BaseCommand):
    help = 'Export the Chat conversations, one TSV file per user'

    def handle(self, **options):
        self.export_conversations()

    def export_conversations(self):
        conversation_dict = {}
        for user in sorted(User.objects.all(), key=lambda u: u.username):
            conversation_dict[user.username] = self.get_conversations(user)

        for username, conversations in conversation_dict.items():
            if not conversations:
                continue

            file_name = f'conversations.{username}.tsv'.replace(' ', '_')
            with open(file_name, 'w') as f:
                writer = csv.writer(f, delimiter='\t',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['DATE', 'USER', 'STYLE', 'DATA', 'TEXT'])
                for conversation in conversations:
                    writer.writerow(conversation)

    def get_conversations(self, user: User) -> List[List[str]]:
        conversations = []
        for message in ChatMessage.objects.filter(roomname=user.username):
            date = datetime.fromtimestamp(message.timestamp / 1000)
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
            text, value, style = self.get_text_data_style(message.text)
            conversations.append(
                [date_str, message.username, style, value, text])
        return conversations

    @staticmethod
    def get_text_data_style(text: str) -> Tuple[str, str, str]:
        try:
            root = etree.fromstring(text)
            text = next(root.itertext())
            style = root.attrib.get('style', '')
            if root.find('data') is not None:
                value = ' '.join(root.find('data').values())
            else:
                value = ''
        except etree.XMLSyntaxError as _:
            text = text
            style = ''
            value = ''

        text = text.strip()
        if text.endswith('\n'):
            text = text[:-1]

        return text, value, style
