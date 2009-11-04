from zope.interface import Interface

class IVersioner(Interface):
    """
    Interface for utility which provides versioning methods
    """

    def getWorkspace(context):
        """If the authenticated member does not have a workspace then create 
        one. Return the workspace.
        
        A context is needed to be able to find the membership tool."""

    def checkout(item):
        """Checkout item to authenticated member's workspace. Returns 
        checked out item."""

    def checkin(item):
        """Checkin item from authenticated member's workspace to 
        repository. Returns checked in item."""
