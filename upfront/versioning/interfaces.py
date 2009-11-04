from zope.interface import Interface

class IVersioner(Interface):
    """
    Interface for utility which provides versioning methods
    """

    def checkout(item):
        """Checkout item to authenticated member's workspace"""

    def checkin(item):
        """Checkin item from authenticated member's workspace to 
        repository"""
