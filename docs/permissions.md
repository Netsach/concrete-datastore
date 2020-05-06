## Permissions

Multiple parameters are put together to determine the permissions that were granted for each user:

- Request Type (scoped/unscoped)
- Model and objects definition
- Scopes of user
- User Level

These criteria are ordered by strength (from the strongest criterion to the weakest).

### Request Type

When performing a request to the API Concrete (get, post, patch, delete), the scope (`X-ENTITY-UID`) can be added to the headers of the request:

The scope passed in the headers of a request is used to filter the response's objects, and allows access only to the objects having the same scope.

#### Unscoped Request

```shell
curl \
  -X GET \
  -H "Authorization: Token b1cccee29710b53386b964d93847648a526005a8" \
  "https://<webapp>/api/v1.1/<model-name>/"
```
#### Scoped Request

```shell
curl \
  -X GET \
  -H "Authorization: Token b1cccee29710b53386b964d93847648a526005a8" \
  -H "X-ENTITY-UID: 7508ffd7-2d10-413e-86b6-4adab3767413" \
  "https://<webapp>/api/v1.1/<model-name>/"
```

**Example:** given two scopes `scopeA` and `scopeB` and a model `MyModel` accessible through a `url`. Given objects:

- `object1: scope=scopeA`
- `object2: scope=scopeB`
- `object3: scope=None`
- `object4: scope=scopeA`

A SuperUser with a token `super_token` makes the request to get a list of the objects of the model `MyModel`.

- **Unscoped Request:** `requests.get(url,headers={"Authorization":"Token {}".format(super_token)})` returns a list of objects within a JSON response, containing all of the four objects.

- **Scoped Request:** `requests.get(url,headers={"Authorization":"Token {}".format(super_token),"X-ENTITY-UID":scopeA.uid})` returns a list containing only the objects with the scope `scopeA` (i.e only `object1` and `object4`).

### Model and Object Definition

#### Model Definition

For a model, some user level constraints are set to determine whether a given user can perform a given operation (create, delete, retrieve and update) or not:

```json
{
  "ext.m_creation_minimum_level": "admin",
  "ext.m_delete_minimum_level": "superuser",
  "ext.m_retrieve_minimum_level": "authenticated",
  "ext.m_update_minimum_level": "manager"
}
```

#### Object Definition

Objects can have arguments that allow a user (or a group of users) to perform some operations that he can't normally perform:


- `can_view_users`, `can_view_groups`: gives `Retrieve` rights to a user or a group of users.
- `can_admin_users`, `can_admin_groups`: gives `Retrieve` and `Update` rights to a user or a group of users.
- `public`: a boolean. If set to false, a user with level `manager` or less can't have access to this object unless he is the owner (`created_by`) or listed in `can_admin_[users/groups]` or `can_view_[users/groups]`.

### User levels

There are five user levels with a set of permissions and privileges:

Superuser > Admin > Manager > Simpleuser > Blocked

- The `superuser` has access to everything and has all the rights.
- The other levels have different create and retrieve permissions, depending on the model and the created instance.
- The `blocked` user has access to nothing.

### User Scopes

A user can have one or more scopes that are used to determine the range of objects accessible to him.

A user of an `admin` level or higher has access to all the objects, independently of his scopes.

For a level `manager` or less, if the user has a scope `A`, he can access to all the objects having a scope `A` (and only these objects).
The possible operations on these objects are those that satisfy the model's definition.


### Example

Given two scopes: `Divider_X` and `Divider_Y`

Given the following users:

- **SuperUser**: without scopes.
- **Admin**: without scopes.
- **Manager**: without scopes.
- **Manager_X**: with scope `Divider_X`.
- **Manager_Y**: with scope `Divider_Y`.
- **Manager_XY**: with scopes `Divider_X` and `Divider_Y`.
- **SimpleUser**: without scopes.
- **SimpleUser_X**: with scope `Divider_X`.
- **SimpleUser_Y**: with scope `Divider_Y`.
- **SimpleUser_XY**: with scopes `Divider_X` and `Divider_Y`.


Given a Divided Model `MyModel` and four instances of this model with the following configuration:

![](./assets/permissions-example.png)

#### 1st case: For A Scoped Request With The Scope Divider_X:

- **SuperUser:** can access to `instance_1` and `instance_3` and has all the rights.
- **Admin:** can access to `instance_1` and `instance_3` and has retrieve, create and update rights
- **Manager:** can access to `instance_3` (because of `can_view_users`) with retrieve rights and `instance_1`(because of `can_admin_users`) with retrieve and update rights
- **Manager_X**: can access to `instance_1` and `instance_3` (because of scope) and has retrieve and update rights
- **Manager_Y**: has access only to `instance_3` (because of `can_admin_users`) and has retrieve and update rights.
- **Manager_XY**: can access to `instance_1` and `instance_3` and has retrieve and update rights
- **SimpleUser**: has access only to `instance_1` (because of `can_view_users`) and has only retrieve rights
- **SimpleUser_X**: has access to `instance_1` and `instance_3` (because of scope) and has only retrieve rights
- **SimpleUser_Y**: has access to nothing
- **SimpleUser_XY**: has access to `instance_1` and `instance_3` (because of scope) and has only retrieve rights

#### 2nd case: For A Scoped Request With The Scope Divider_Y:

- **SuperUser:** can access to `instance_2` and has all the rights.
- **Admin:** can access to `instance_2` and has retrieve, create and update rights
- **Manager:** has access to nothing
- **Manager_X**: can access to `instance_2` (because of `can_view_users`) and has only retrieve rights
- **Manager_Y**: has access to `instance_2` (because of scope) and has retrieve and update rights.
- **Manager_XY**: can access to `instance_2` and has retrieve and update rights
- **SimpleUser**: has access `instance_2` (because of `can_admin_users`) and has only retrieve rights
- **SimpleUser_X**: has access to nothing
- **SimpleUser_Y**: has access to `instance_2` with retrieve rights
- **SimpleUser_XY**: has access to `instance_2` (because of scope) and has only retrieve rights

#### 3rd case: For A Non-Scoped Request:

- **SuperUser:** can access to everything and has all the rights.
- **Admin:** can access to everything and has retrieve, create and update rights
- **Manager:** can access to `instance_3` (because of `can_view_users`) with retrieve rights and `instance_1`(because of `can_admin_users`) with retrieve and update rights
- **Manager_X**: can access to `instance_2` (because of `can_view_users`) with only retrieve rights, and can access to `instance_1` and `instance_3` (because of scope) with retrieve and update rights
- **Manager_Y**: has access to `instance_2` (because of scope) and to `instance_3` (because of `can_admin_users`) and has retrieve and update rights.
- **Manager_XY**: can access to everything and has retrieve and update rights
- **SimpleUser**: has access `instance_2` (because of `can_admin_users`) and `instance_1` (because of `can_view_users`) and has only retrieve rights
- **SimpleUser_X**: has access to `instance_1` and `instance_3` (because of scope) as well as `instance_4` (because of public) and has only retrieve rights
- **SimpleUser_Y**: has access to `instance_2` (because of scope) and `instance_4` (because of public) with retrieve rights
- **SimpleUser_XY**: has access to everything (because of scopes and public) and has only retrieve rights

