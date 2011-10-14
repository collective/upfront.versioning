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

    # make sure nothing is left uncataloged
    pc = getToolByName(item, 'portal_catalog')
    for brain in pc(path='/'.join(item.getPhysicalPath()),
                    portal_type='Discussion Item'):
        pc.uncatalog_object(brain.getPath())

def afterATObjectCheckoutEvent(ob, event):   
    # Fix references. Fields that have keepReferencesOnCopy set do not 
    # need to be fixed.
    original = event.original
    for field in original.Schema().fields():
        if (field.type == 'reference'):
            accessor = field.getAccessor(original)
            original_value = accessor()
            accessor = field.getAccessor(ob)
            new_value = accessor()
            if new_value != original_value:
                field.set(ob, original_value)

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

    # Did a move take place?
    if (event.oldParent is not None) and (event.newParent is not None) \
        and event.oldName and event.newName:

        vc = getToolByName(event.oldParent, 'upfront_versioning_catalog', None)
        if vc is not None:

            # Uncatalog everything under the object being renamed
            if ob == event.object:
                pth = '/'.join(event.oldParent.getPhysicalPath()) + '/' + event.oldName
                for brain in vc.unrestrictedSearchResults(path=pth):
                    vc.uncatalog_object(brain.getPath())

            # Catalog objects affected by rename. Method catalog_object 
            # will not index objects not subjected to versioning, so we 
            # don't have to check anything here.
            vc.catalog_object(ob, '/'.join(ob.getPhysicalPath()))

    # Did a delete take place?
    elif (event.oldParent is not None) and event.oldName:

        vc = getToolByName(event.oldParent, 'upfront_versioning_catalog', None)
        if vc is not None:

            # Uncatalog everything under the object being renamed
            if ob == event.object:
                pth = '/'.join(event.oldParent.getPhysicalPath()) + '/' + event.oldName
                for brain in vc.unrestrictedSearchResults(path=pth):
                    vc.uncatalog_object(brain.getPath())
