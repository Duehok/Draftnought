"""Helper classes for everybody"""
from abc import ABC, abstractmethod

class Command(ABC):
    """base class for the commands

    used to implemnt undo/redo queues
    Subclasses must implement the execute() and undo() methods
    """
    def __init__(self):
        pass

    @abstractmethod
    def execute(self):
        """execute the command"""
        pass

    @abstractmethod
    def undo(self):
        """undo the command"""
        pass

class CommandStack:
    """Undo/redo stacks for command pattern"""
    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []

    def do(self, command):
        """Execute the command, add it to the undo stack
        And purge the redo stack
        """
        self._redo_stack = []
        self._undo_stack.append(command)
        command.execute()

    def undo(self):
        """Undo the command on top of the undoing stack
        Then add is on to of the redo stack

        If undo stack is empty, do nothing
        """
        if self._undo_stack:
            command = self._undo_stack.pop()
            self._redo_stack.append(command)
            command.undo()

    def redo(self):
        """Redo the command on top of the redoing stack
        Then add is on to of the undo stack

        If redo stack is empty, do nothing
        """
        if self._redo_stack:
            command = self._redo_stack.pop()
            self._undo_stack.append(command)
            command.execute()

class Observable:
    """Observable for the observer pattern"""
    def __init__(self):
        self._subscribers = []

    def subscribe(self, callback):
        """Called from a subscriber to subscribe to the notifications from an observable object

        Args:
            callback (method): the function that should be called when a notification is send
                callback should be analog to:
                def callback(self, observable_object, event_type, dict_with_event_info)
        Returns:
            an unsuscribe function that should be called to stop receiving notification
            to the callback
        """
        self._subscribers.append(callback)

        def _unsubscribe():
            """The callback won't receives the subscriptions anymore
            """
            #TODO: test this!
            self._subscribers.remove(callback)

        return _unsubscribe

    def _notify(self, event_type, event_info):
        """The observalbe object should run this method to notify the subscribers

        Args:
            event_type (str): event type identifier
            event_info (dict): schema should depend on the event type,
                and contains all that the subscribers need
        """
        for call in self._subscribers:
            call(self, event_type, event_info)

class Subscriber(ABC):
    """Subscriber for the observer pattern

    Args:
        observable: an object whose class inherits Observable
    """
    def __init__(self, observable):
        self.unsubscribe = observable.subscribe(self._on_notification)

    @abstractmethod
    def _on_notification(self, observable, event_type, event_info):
        """Called by the notifications from the observable object

        Args:
            observable (Observable): the notifying object
            type (str): event type identifier
            event_info (dict): a dict specific to the event type
                with all the data needed for the subscriber to do its work
        """
        pass

def is_int(possible_number):
    """Returns true if the passed string can be parsed to an int, false if not

    Args:
    possible_number (str):
    """
    try:
        int(possible_number)
        return True
    except ValueError:
        return False
