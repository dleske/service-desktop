# Service Desktop

Flask app with jQuery and Bootstrap, Postgres on the back end.

Use cards to show web apps and sites available to the visitor.  Cards would be
bilingual and show application name, brief description, operational status,
and buttons for such as additional information or to launch the application
(in a separate window named for the application).

It might help to flag whether an app is SSO-enabled, with explanatory text
available.

Cards would be organized by access level or functional area (account, help,
administrative, etc.) and sorted by recent use (recency and frequency). 

## Project status

This was an experimental project which has had its organization-specific
components and code yanked out.  As such the current codebase will not work.
Watch for this notice to disappear.

### Base functionality

* [x] Basic listing of services loaded into database
* [x] User personalization: showing only what user can access
* [ ] User personalization: tracking service launches
* [ ] User personalization: sorting cards by recency and frequency
* [x] SSO flag
* [ ] Generic service flags
* [ ] Management API
* [ ] Integration testing

## Service definitions

Service
- name
- url
- SSO and other operational flags (maybe a separate table)

Service description
- service
- language
- title
- description

Service access
- service
- category (accounts, support and documentation, admin, ...)
- access requirement string--this could be an LDAP query for example

URL may actually differ by language.

Service descriptions should be written specifically for the user.  Even in the
context of the service catalogue, this helps communicate the _value_ of the
application or service to the user, rather than a flat description or listing
of features.

## API

RESTful API.

### Development and "direct" API access

For developing AJAX API, support direct manipulation using a modal that
presents an endpoint (route), method, and a JSON field.  Clearly use of the
routes provided by this API need to be governed by necessary access control,
but this would support proving the use of the API, a measure of
reproducibility, and a means to effect changes before all UX elements are in
place, but without resorting to database manipulation.

Use PUT for these--PUT must be idempotent.  So can just keep re-uploading the
same stuff.
