from zope.interface import implements
from zope.component.interfaces import ObjectEvent

from interfaces import IVersioningEvent, IBeforeObjectCheckoutEvent, \
    IAfterObjectCheckoutEvent, IBeforeObjectCheckinEvent, \
    IAfterObjectCheckinEvent

class VersioningEvent(ObjectEvent):
    implements(IVersioningEvent)

class BeforeObjectCheckoutEvent(VersioningEvent):
    implements(IBeforeObjectCheckoutEvent)

class AfterObjectCheckoutEvent(VersioningEvent):
    implements(IAfterObjectCheckoutEvent)

    def __init__(self, object, original):
        VersioningEvent.__init__(self, object)
        self.original = original

class BeforeObjectCheckinEvent(VersioningEvent):
    implements(IBeforeObjectCheckinEvent)

class AfterObjectCheckinEvent(VersioningEvent):
    implements(IAfterObjectCheckinEvent)

    def __init__(self, object, original):
        VersioningEvent.__init__(self, object)
        self.original = original

