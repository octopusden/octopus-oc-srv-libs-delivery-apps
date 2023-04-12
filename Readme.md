# Delivery portal models for Django.

## Checksums and dlcontents

![Checksums data model]("checksums-diagram.png")

For tests to work **sqlite** is to be installed, version *3.20* at least.
Implemented as classic Django applications but with direct *SQL* commands for creation of unique database indexes for some tables, see *migrations* sub-folders.

*ORM* initialization should be done before usage, so *oc-orm-initializator* is necessary:

```
from cdt_orm_initializator.orm_initializator import OrmInitializator
#...
_installed_apps=["oc_delivery_apps.checksums"]
OrmInitializator(
            url=_args.psql_url,
            user=_args.psql_user,
            password=_args.psql_password,
            installed_apps=_installed_apps)

```
***NOTE***:  It is a bad idea to put *checksums* and *dlcontents* databases in the same schema, so example above does not include both simultaneously.

### GroupId for Documentation and Release Notes
Calculation templates:

- **DOC**: `${MVN_PREFIX}.${MVN_DOC_SUFFIX}.documentation`
- **RN**: `${MVN_PREFIX}.${MVN_RN_SUFFIX}.release_notes`

This means *MVN_PREFIX*, *MVN_DOC_SUFFIX* and *MVN_RN_SUFFIX* should be set before calling the corresponding routies.
