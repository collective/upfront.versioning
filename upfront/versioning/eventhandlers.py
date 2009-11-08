"""Default event handlers. A typical custom use case would be to delete 
comments when an object is chacked out. It is left as an exercise to the 
reader :)"""

import logging

from Products.CMFCore.utils import getToolByName

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