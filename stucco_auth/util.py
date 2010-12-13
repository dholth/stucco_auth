"""
Utility functions.
"""

import collections
import logging

class Message(collections.namedtuple('Message', 'text flash_type')):
    def __str__(self):
        return self.text

class Flasher(object):

    def __init__(self, request):
        self.request = request

    @property
    def messages(self):
        return self.request.session.get('flash', [])

    def __len__(self):
        return len(self.messages or [])

    def pop(self):
        msgs = self.messages or []
        if len(msgs) > 0:
            return msgs.pop()
        return None

    def add(self, message, flash_type=logging.INFO):
        messages = self.messages or []
        self.request.session['flash'] = messages
        messages.append(Message(message, flash_type))

    def pop_iter(self):
        while len(self.messages) > 0:
            yield self.messages.pop()

    def __str__(self):
        return '<Flasher message_count=%i>' % len(self)
    __repr__ = __str__
