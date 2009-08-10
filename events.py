#
#
# vim: ts=4 sw=4 sts=0 expandtab:
import os
import copy
import logging
import weakref

import generator

logger = logging.getLogger(__name__)

class Event(object):
    """
    This is a simple object which represent an event it can be dispatched which
    notifies every observer of this event
    """
    name = ""
    types = None
    def __init__(self, *args):
        """
        Init procedure
        """
        self.clear()
        self.uid_gen = generator.uid_generator()
        if len(args) != 0:
            self.types = args

    def addObserver(self, obj, *args, **kwarg):
        """
        This method add an observer for this event. Every argument passed to
        this function will be forwarded to the callback when the event is fired
        """
        if not callable(obj):
            raise RuntimeError("Callback must be callable")

        oid = self.uid_gen.next() if 'id' not in kwarg else kwarg.pop('id')
        self.observers[oid] = (weakref.ref(obj), args)
        return oid

    def removeObserver(self, obj):
        """
        This method remove an observer for the event.
        """
        del self.observers[obj]

    def dispatch(self, *args):
        """
        This method dispatch the events with arguments which are forwarded to
        the listener functions.
        """
        o2 = copy.copy(self.observers)
        for id, (wcallback, cargs) in o2.iteritems():
            try:
                callback = wcallback()
                if callback is not None:
                    callback(*(args + cargs))
                else:
                    if logger.isEnabledFor(logging.WARNING):
                        logger.warning("Observer event deleted id [%d]" % id)
                        print args
                    del self.observers[id]
            except Exception, e:
                logger.exception(str(e))

    def __call__(self, *args):
        self.dispatch(*args)

    def clear(self):
        """
        Clear the observer dictionary.
        """
        self.observers = {}

    def __len__(self):
        return len(self.observers)

ThreadsafeEvent = Event

class EventDispatcherBase(object):
    """
    This object act as a base object for an aglomerate of events. It provides
    the possibility tp register a single object for every events in the object.
    It is also in charge of initializing events.
    """
    events = []
    event_type = Event
    def __init__(self):
        """
        Simple Init method which creates the events
        """
        for evt_name in self.events:
            if hasattr(self, evt_name + "Event"):
                    logger.warning("Event Function Override -- %s --" % evt_name)
            else:
                evt = self.event_type()
                setattr(self, evt_name + "Event", evt)
                evt.name = evt_name

    def addObserver(self, obj, *args, **kw):
        """
        Add the right method observer to the contained event
        """
        for evt in self.events:
            try:
                getattr(self, evt + "Event").addObserver(getattr(obj, evt), *args, **kw)
            except AttributeError, err:
                if logger.isEnabledFor(logging.WARNING):
                    logger.warning("Object : %s do not have attribute -- %s --" % \
                               (repr(obj), evt))

    def removeObserver(self, obj):
        """
        Remove the right method observer to the contained event
        """
        for evt in self.events:
            try:
                getattr(self, evt).removeObserver(getattr(obj, evt), evt, *args, **kw)
            except AttributeError, err:
                if logger.isEnabledFor(logging.WARNING):
                    logger.warning("Object : %s do not have attribute -- %s --" % \
                               (repr(obj), evt))

    def clear(self):
        """
        Clear all events of this object
        """
        for evt in self.events:
            getattr(self, evt + "Event").clear()

    def dispatch(self, evtname, *args):
        if evtname in self.events:
            getattr(self, evtname + "Event")(*args)


class ThreadsafeEventDispatcher(EventDispatcherBase):
    event_type = ThreadsafeEvent

