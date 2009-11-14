"""Default event handlers. A typical custom use case would be to delete 
comments when an object is checked out. It is left as an exercise to the 
reader :)"""

import logging
from DateTime import DateTime
from Acquisition import aq_base

from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.interfaces.IStorage import StoragePurgeError

from upfront.versioning import _

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
            u"Reference ${plurality} ${fields} will not keep its value after the item is checked out",
            mapping={
                'plurality':(len(problems) > 1) and 'fields' or 'field',
                'fields': ', '.join([f.getName() for f in problems])
            }
        )
        msg = u"Reference %s %s will not keep its value after the item is checked out" \
            % ((len(problems) > 1) and 'fields' or 'field', ', '.join([f.getName() for f in problems]))
        logger = logging.getLogger('upfront.versioning')
        logger.warn(msg)
        getToolByName(ob, 'plone_utils').addPortalMessage(msg, type='warn')

def afterATObjectCheckoutEvent(ob, event):
    # Remove workflow history
    unwrapped = aq_base(ob)
    if hasattr(unwrapped, 'workflow_history'):
        unwrapped.workflow_history = {}
   
    # Catalog checked out item
    vc = getToolByName(ob, 'upfront_versioning_catalog')
    vc.catalog_object(ob)

def beforeATObjectCheckinEvent(ob, event):
    # Uncatalog checked out item
    vc = getToolByName(ob, 'upfront_versioning_catalog')
    vc.uncatalog_object('/'.join(ob.getPhysicalPath()))

def afterATObjectCheckinEvent(ob, event):
    # Remove CMFEditions history    
    tool = getToolByName(ob, 'portal_repository', None)
    if tool is not None:
        for h in tool.getHistory(ob):
            tool.purge(ob, h.version_id)

    # Catalog checked in item
    vc = getToolByName(ob, 'upfront_versioning_catalog')
    vc.catalog_object(ob)

    # Expire all other versions of this item. Doing so prevents 
    # portal_catalog from returning older versions unless it is 
    # specifically instructed to do so.
    portal = getToolByName(ob, 'portal_url').getPortalObject()
    expires = DateTime() - 1/1440.0
    for brain in vc.getVersionsOf(ob):
        o = brain.getObject()
        if o == ob:
            # Skip over context
            continue
        if not portal.isExpired(o):
            o.setExpirationDate(expires)
            o.reindexObject()
