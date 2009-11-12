from zope.interface import Interface, Attribute
from zope.component.interfaces import IObjectEvent
from zope.annotation.interfaces import IAnnotations

class IVersioner(Interface):
    """Interface for utility which provides versioning methods"""

    def getWorkspace(context):
        """If the authenticated member does not have a workspace then create 
        one. Return the workspace.
        
        A context is needed to be able to find the membership tool.
        """

    def checkout(item):
        """Checkout item to authenticated member's workspace. Returns 
        checked out item.
        """

    def checkin(item):
        """Checkin item from authenticated member's workspace to 
        repository. Returns checked in item.
        """

class ICheckedOut(Interface):
    """Marker interface applied to an object on checkout"""

class IVersionMetadata(IAnnotations):
    """Interface for adapter which manages version metadata on an object """

    def initialize(item):
        """Set values obtained from item"""

    def token():
        """Return an identifier that can be used to find the original item.
        The word 'token' is used since UID is Archetypes specific and we want 
        to be agnostic.
        """

class IVersioningEvent(IObjectEvent):
    """Base class for versioning events"""

class IBeforeObjectCheckoutEvent(IVersioningEvent):
    pass

class IAfterObjectCheckoutEvent(IVersioningEvent):
    original = Attribute(u"The object that was originally cloned to create the copy")

class IBeforeObjectCheckinEvent(IVersioningEvent):
    pass

class IAfterObjectCheckinEvent(IVersioningEvent):
    original = Attribute(u"The object that was originally cloned to create the copy")
