from zope.interface import implements, alsoProvides

from Products.CMFCore.utils import getToolByName

from interfaces import IVersioner

class Versioner(object):
    """
    Provide versioning methods
    """
    implements(IVersioner)

    def checkout(self, item):
        pass

    def checkin(self, item):
        pass
