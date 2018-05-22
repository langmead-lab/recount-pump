#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import abc


class Service(abc.ABC):

    @abc.abstractmethod
    def get(self, queue):
        pass

    @abc.abstractmethod
    def queue_create(self, name):
        pass

    @abc.abstractmethod
    def queue_exists(self, name):
        pass

    @abc.abstractmethod
    def queue_delete(self, name, if_empty=False):
        pass

    @abc.abstractmethod
    def ack(self):
        pass

    @abc.abstractmethod
    def publish(self, queue, message):
        pass

