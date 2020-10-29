# -*- coding: utf-8 -*-
__author__ = 'Martin Pihrt'

# Local imports
from ospy.options import options


class _User(object):
    SAVE_EXCLUDE = ['SAVE_EXCLUDE', 'index', '_users']

    def __init__(self, users_instance, index):
        self._users = users_instance
 
        self.name = ""            # user name
        self.password_hash = ""   # hashed user password
        self.password_salt = ""   # salt for user password
        self.password_time = 0    # current password decryption time (brute force)
        self.category = 0         # selector (public, user, admin)
        self.notes = ""           # notes for user


    @property
    def index(self):
        try:
            return self._users.get().index(self)
        except ValueError:
            return -1     

    def __setattr__(self, key, value):
        super(_User, self).__setattr__(key, value)
        if key not in self.SAVE_EXCLUDE:
            if self.index >= 0:
                options.save(self, self.index)                            
                

class _Users(object):
    def __init__(self):
        self._users = []

        i = 0
        while options.available(_Users, i):
            self._users.append(_User(self, i))
            i += 1

    def add_users(self, user=None):
        try:
            if user is None:
                user = _User(self, len(self._users))
            self._users.append(user)
            options.save(user, user.index)
        except:
            pass

    def create_users(self):
        """Returns a new users, but doesn't add it to the list."""
        try:
            return _User(self, -1-len(self._users))
        except:
            pass       

    def remove_users(self, index):
        try:
            if 0 <= index < len(self._users):
                del self._users[index]

            for i in range(index, len(self._users)):
                options.save(self._users[i], i)     # Save users using new indices

            options.erase(_User, len(self._users))  # Remove info in last index
        except:
            pass

    def count(self):
        return len(self._users)

    def get(self, index=None):
        try:
            if index is None:
                result = self._users[:]
            else:
                result = self._users[index]
            return result
        except:
            pass

    __getitem__ = get

users = _Users()
