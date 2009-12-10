from plone.indexer import indexer
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import allowedRolesAndUsers
from interfaces import ICheckedOut

@indexer(IContentish)
def content_allowedRolesAndUsers(object):
    """Restrict allowedRolesAndUsers severely for a new version of an item"""
    parent = object
    while parent is not None:    
        if ICheckedOut.providedBy(parent):
            pms = getToolByName(object, 'portal_membership')
            member = pms.getAuthenticatedMember()
            return ['user:%s' % member.getId()]
        parent = getattr(parent, 'aq_parent', None)

    return allowedRolesAndUsers(object)
