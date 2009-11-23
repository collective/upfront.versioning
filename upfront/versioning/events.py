from zope.interface import implements
from zope.component.interfaces import ObjectEvent

from interfaces import IVersioningEvent, IBeforeObjectCheckoutEvent, \
    IAfterObjectCheckoutEvent, IBeforeObjectDeriveEvent, IAfterObjectDeriveEvent, \
    IBeforeObjectCheckinEvent, IAfterObjectCheckinEvent

class VersioningEvent(ObjectEvent):
    implements(IVersioningEvent)

class BeforeObjectDeriveEvent(VersioningEvent):
    implements(IBeforeObjectDeriveEvent)

class AfterObjectDeriveEvent(VersioningEvent):
    implements(IAfterObjectDeriveEvent)

    def __init__(self, object, original):
        VersioningEvent.__init__(self, object)
        self.original = original

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

