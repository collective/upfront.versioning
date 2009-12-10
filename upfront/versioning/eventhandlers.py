"""Default event handlers. Subscribe to these events in a third party 
application.
"""

import logging
from DateTime import DateTime
from Acquisition import aq_base

from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IStorage import StoragePurgeError

from upfront.versioning import _

def _removeDiscussion(item):
    """Remove discussion from item"""
    tool = getToolByName(item, 'portal_discussion')
    if tool.isDiscussionAllowedFor(item):
        # _createDiscussionFor has a handy side effect of clearing the 
        # discussion
        tool._createDiscussionFor(item)

def beforeATObjectCheckoutEvent(ob, event):
    """Iterate over object's schema fields and warn for every reference 
    field that does not have keepReferencesOnCopy set to true and whose 
    value is set."""
    problems = []
    for field in ob.Schema().fields():
        if (field.type == 'reference') and not field.keepReferencesOnCopy:
            # Ignore if no value is set
            accessor = field.getAccessor(ob)
            if accessor():
                problems.append(field)

    if problems:                
        # todo: figure out why mapping replacement does not work
        msg = _(
            u"Reference ${plurality} ${fields} will not keep its value",
            mapping={
                'plurality':(len(problems) > 1) and 'fields' or 'field',
                'fields': ', '.join([f.getName() for f in problems])
            }
        )
        msg = u"Reference %s %s will not keep its value" \
            % ((len(problems) > 1) and 'fields' or 'field', ', '.join([f.getName() for f in problems]))
        logger = logging.getLogger('upfront.versioning')
        logger.warn(msg)
        getToolByName(ob, 'plone_utils').addPortalMessage(msg, type='warn')

def afterATObjectCheckoutEvent(ob, event):   
    # Expire checked out item
    # xxx: abuse allowedRolesAndUsers

    # Remove discussion
    _removeDiscussion(ob)
    
def afterATObjectCheckinEvent(ob, event): 
    portal = getToolByName(ob, 'portal_url').getPortalObject()
    
    # Un-expire current version
    if portal.isExpired(ob):
        ob.setExpirationDate(None)
        ob.reindexObject()

    # Expire all other versions of this item. Doing so prevents 
    # portal_catalog from returning older versions unless it is 
    # specifically instructed to do so.
    vc = getToolByName(ob, 'upfront_versioning_catalog')
    expires = DateTime() - 1/1440.0
    for brain in vc.getVersionsOf(ob):
        o = brain.getObject()
        if o == ob:
            # Skip over context
            continue
        if not portal.isExpired(o):
            o.setExpirationDate(expires)
            o.reindexObject()

def onATObjectMovedEvent(ob, event):
    """Objects need to be recatalogued or removed when moves and 
    deletes occur"""

    if event.oldParent and event.newParent and event.oldName and event.newName:
        # A move took place. Catalog only if object is already in the catalog.
        vc = getToolByName(event.oldParent, 'upfront_versioning_catalog', None)
        if vc is not None:
            pth = '/'.join(event.oldParent.getPhysicalPath()) \
                + '/' +event.oldName
            if vc.isCatalogued(pth):
                vc.uncatalog_object(pth)
                vc.catalog_object(
                    ob, 
                    '/'.join(ob.getPhysicalPath()),
                    skip_interface_check=True
                )
        
    elif event.oldParent and event.oldName:
        # A delete took place
        vc = getToolByName(event.oldParent, 'upfront_versioning_catalog', None)
        if vc is not None:
            pth = '/'.join(event.oldParent.getPhysicalPath()) \
                + '/' +event.oldName
            if vc.isCatalogued(pth):
                vc.uncatalog_object(pth)
