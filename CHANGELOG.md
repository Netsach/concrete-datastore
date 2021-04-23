# Changelog

## [Unreleased]

### Added

- nothing added

### Changed

- nothing changed

### Removed

- nothing removed

## [1.28.0] - 2021-03-15

### Changed

- Allow NULL values for FileField and PointField serializer

## [1.27.0] - 2021-02-24

### Changed

- Use OpenStreetMap for admin PointField

## [1.26.0] - 2021-02-19

## [1.25.0] - 2021-02-18

### Added

- Add utf8 encoding while loading datamodel
- GeoDjango PointField to compute distances

## [1.24.0] - 2021-02-15

### Added

- New field type `ip`

## [1.23.0] - 2021-01-14

### Added

- Add checks on the url_format for reset password view to avoid template injections

## [1.22.0] - 2021-01-13

### Added

- Add checks on the levels of users that are allowed to set an email_format when reset password
- Add checks on the url_format to avoid template injections

## [1.21.0] - 2021-01-13

### Added

- Enable admin url view with settings

### Changed

- Change staff to manager in CRUD_LEVELS

## [1.20.0] - 2020-12-07

## [1.19.0] - 2020-12-07

### Added

- Added the capability to authenticate using `c_auth_with_token` query parameter in urls when using HTTP headers is not possible (webhooks).

## [1.18.0] - 2020-11-30

## [1.17.0] - 2020-11-30

### Changed

- Update pillow package version to `>=8` to support python3.7 and later

## [1.16.1] - 2020-10-27

## [1.16.0] - 2020-10-27

### Added

- Add API filters for ManyToMany fields using the `__in` filter
- Fix the Swagger generator to include all the queryparams

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
