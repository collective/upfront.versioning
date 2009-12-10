Introduction 
============
CMFEditions is the de facto Plone versioning system but it does not treat 
old versions as first-class objects. Old versions cannot be found with the 
portal_catalog and, crucially, cannot be referenced by other objects.

upfront.versioning solves this problem. There is no central repository - 
versions are by default siblings of a version aware container. 

Operation 
========= 
upfront.versioning introduces two operations surfaced as actions in the Plone
site. These are "Start new version" and "Commit". The product is configured 
from the Control Panel.

A. Start new version

This operation is available if the user may edit the item and the content 
type is configured to be versionable.

If an item (eg. foo) has not yet been versioned then a version container called 
foo replaces the item. This container has two children: 00000001 is the original item 
and 00000002 is the new version.

If an item (eg. foo/00000005) has been versioned then a new version foo/00000006 
is created.

A newly created version is only available to the user who created it. It does not 
appear in searches. Its workflow is locked down during authoring.

B. Commit

This operation is available if the user may edit the item, the content type 
is configured to be versionable and the item was in fact created by starting 
a new version.

The item becomes the latest version. It may appear in searches. Old versions are 
expired. The latest version is the only item that is subject to workflow - all 
other versions are locked down.

User interface 
============== 
The product is configured at @@upfront.versioning-settings.

A versions viewlet is present at the bottom of every item that (a) is of a
portal type configured to be subject to versioning and (b) has version
information.  It is loaded lazily with ajax since it can be slow.

Design
======
Versioning is realized through a combination of marker interfaces, annotations 
and a versioning catalog. 

Read DESIGN.txt for details.
