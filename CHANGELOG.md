# Changelog

## [Unreleased]

### Added

- nothing added

### Changed

- nothing changed

### Removed

- nothing removed

## [1.15.0] - 2020-10-20

### Changed

- In swagger-ui view, you can either authorize with `Token XXX` or `XXX`. Both are accepted

## [1.14.0] - 2020-10-20

### Added

- Add button in admin site to switch to Core Admin view if core automation is enabled

### Changed

- Changed filtering of m2m fields in the admin view to horizontal filtering
- Changed the `/stats` enpoint to return proper list of urls

## [1.13.0] - 2020-07-17

### Changed

- Fixed the special characters list to avoid string-formatting errors because of the `%`
- Simpleuser can see the field `scopes` of every instances

## [1.12.0] - 2020-07-08

### Changed

- use `object_name` instead of `name` to rearrange the admin models in categories

## [1.11.0] - 2020-07-08

### Added

- Add error codes to concrete API 400_BAD_REQUEST responses

## [1.10.0] - 2020-07-07

### Added

- When deleting a SecureConnectToken, ignore creation of a DeletedModel.
- Added a setting IGNORED_MODELS_ON_DELETE for the models to ignore when deleting.

### Changed

- Do not exclude the recently created objects for requests with `timestamp_start`
- Fixed api logs format with the version 2 of pendulum

## [1.9.0] - 2020-06-16

### Changed

- Enhanced the information returned by the `/stats/` endpoint by the following fields: `num_total_pages`, `max_allowed_objects_per_page`, and `pages_urls`
- Fix fetching the divider model for an anonymous user if the minimum retrieve level is anonymous

## [1.8.0] - 2020-04-28

### Added

- Enable the use of Workflows within a core installed in concrete

## [1.7.0] - 2020-03-30

### Changed

- Pendulum version updgraded to v2.0

## [1.6.0] - 2020-03-20

### Added

- Add url to allow a process to register itself to the datatsore

### Changed

- Changed sample datamodel with a simpler one
- Added mini term sheet for README.md
- Reduced log level for legacy behavior
- Explicitly pass exception for legacy behavior

## [1.5.0] - 2020-03-10

### Added

- CSV Export added in admin actions

## [1.4.0] - 2020-03-04

### Added

- Fix error when an user not authenticated access the admin views

## [1.3.0] - 2020-03-03

### Changed

- In CharField and TextField serializers, the field is required only if `blank` is `False` AND default value is not an empty string. Otherwise it is not required.
- admin view rearranged

## [1.2.0] - 2020-02-21

## [1.1.1] - 2020-02-21

## [1.1.0] - 2020-02-21

### Changed

- fixed password change token expiry computation
- fixed register serializer to allow null values of url_format and email_format
- register email subject in settings

## [1.0.1] - 2020-02-21

## [1.0.0] - 2020-02-20

### Added

- concrete datastore doc is up to date.
- Open the sources.
