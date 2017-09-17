import os
import pickle
import errno
import time

__author__ = 'dushyant'


class FileData(object):

    def __init__(self, file_name, timestamp, serverip, event_type):
        self.name = file_name
        self.timestamp = timestamp
        self.serverip = serverip
        self.event_type = event_type


class PersistentSet(object):
    """
    override set to add persistence using pickle
    """

    def __init__(self, pkl_filename):
        self.pkl_filename = pkl_filename
        self.timestamp = None
        try:
            pkl_object = open(self.pkl_filename, 'rb')
            os.chmod(self.pkl_filename, 0777)
            self.set = pickle.load(pkl_object)
        except:
            self.set = set()

    def add(self, element):
        self.set.add(element)
        pkl_object = open(self.pkl_filename, 'wb')
        os.chmod(self.pkl_filename, 0777)
        pickle.dump(self.set, pkl_object)
        pkl_object.close()

    def remove(self, element):
        self.set.remove(element)
        pkl_object = open(self.pkl_filename, 'wb')
        os.chmod(self.pkl_filename, 0777)
        pickle.dump(self.set, pkl_object)
        pkl_object.close()

    def list(self):
        return list(self.set)

    def get_modified_timestamp(self):
        try:
            pkl_object = open(self.pkl_filename, 'rb')
        except IOError as e:
            if e.errno == errno.ENOENT:
                return 0
            else:
                raise
        try:
            pickle.load(pkl_object)
            timestamp = pickle.load(pkl_object)
            return timestamp
        except EOFError:
            return 0


class FilesPersistentSet(PersistentSet):
    """
    override set to add persistence using pickle
    """

    def __init__(self, pkl_filename):
        super(FilesPersistentSet, self).__init__(pkl_filename)

    def add(self, file_name, timestamp, event_type=None, serverip):
        super(FilesPersistentSet, self).add(FileData(filename, timestamp,
                                                     event_type, serverip))

    def remove(self, file_name):
        for filedata in list(self.set):
            if file_name == filedata.name:
                self.set.remove(filedata)
