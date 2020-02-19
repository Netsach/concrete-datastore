## API routes, methods and responses

For all the routes listed below, the API response has the following **failure status codes**:

- `401 UNAUTHORIZED`: if the user has not the rigths to access the data.
- `403 FORBIDDEN`: if the user is not authenticated to the API.
- `404 NOT FOUND`: if the url is not found.

### Custom ConcreteServer endpoints

As explained in the introduction, Concrete Datastore consumes a datamodel definition in order to generate an API giving acess to the instances of the datastore. For each model, ConcreteServer generates andpoints that allow a user to perform **CRUD** methods. this endpoint is a `kebab-case` (lower case with hyphens) of the model's name, for example if you have a model named `MyModel`, the API endpoint will be `my-model`.

For each model, ConcreteServer exposes two routes accepting different methods:

#### List of all instances of model MyModel

##### `GET` :

- **Request**: retrieve all instances of the model

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "http://<webapp>/api/v1.1/my-model/"
```

- **Response**: `200 OK`:

```json
{
  "objects_count": 125,
  "next": "http://<webapp>/api/v1.1/my-model/?page=2",
  "previous": null,
  "results": [
    ...
  ],
  "objects_count_per_page": 125,
  "num_total_pages": 22,
  "num_current_page": 1,
  "max_allowed_objects_per_page": 250,
  "model_name": "MyModel",
  "model_verbose_name": "MyModel",
  "list_display": [],
  "list_filter": {},
  "total_objects_count": 2663,
  "create_url": "http://<webapp>/api/v1.1/my-model/"
}
```

The JSON response contains the following keys:

- `objects_count`: number of objects found in this current page
- `next`: URL to the next page (null if the current page is the last/only page)
- `previous`: URL to the previous page (null if the current page is the first/only page)
- `results`: list of all the instances
- `objects_count_per_page`: pagination of the response
- `num_total_pages`: number of total pages
- `num_current_page`: index of the current page
- `max_allowed_objects_per_page`: max instances to be shown in one page
- `model_name`: model name
- `model_verbose_name`: model verbose name
- `list_display`: list of displayed fields (defined in the datamodel)
- `list_filter`: mapping of the filter fields with `{field_name: field_type}`. Filter fields are defined in the datamodel
- `total_objects_count`: total instances of the current model
- `create_url`: url for instance creation (with a `POST` request)

**IMPORTANT:** For model **User**, the list won't contain any user with the level `blocked`. In order to access these users, see [blocked users](#Blockedusers)

##### `POST` :

- **Request**: Create a new instance of the model.

```shell
curl \
    -X POST \
    -H "Authorization: Token <auth_token>" \
    -d "<JSON data for the new instance to create>" \
    "http://<webapp>/api/v1.1/my-model/"
```

- **Responses**: `201 CREATED` a JSON containing the fields of the new instance created.

**IMPORTANT:** For model **User**, `POST` request is not allowed. In order to create a new user, you should perform a [register](#Register)

#### Specific instance of model MyModel with a UID:

##### `GET`:

- **Request**: Retrieve one instance of model `MyModel` with the given UUID:

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "http://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

- **Response**: `200 OK` a JSON containing the fields of the instance requested.

#### `PATCH`:

- **Request**: Retrieve one instance of model `MyModel` with the given UUID:

```shell
curl \
  -X PATCH \
  -H "Authorization: Token <auth_token>" \
  -d "<JSON data to update>" \
  "http://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

- **Response**: `200 OK` a JSON containing the fields of the instance requested.

#### `PUT`:

- **Request**: Retrieve one instance of model `MyModel` with the given UUID:

```shell
curl \
  -X PUT \
  -H "Authorization: Token <auth_token>" \
  -d "<JSON full data containing data to update>" \
  "http://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

- **Response**: `200 OK` a JSON containing the fields of the instance requested.

#### `DELETE`:

- **Request**: Retrieve one instance of model `MyModel` with the given UUID:

```shell
curl \
  -X DELETE \
  -H "Authorization: Token <auth_token>" \
  "http://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

- **Responses**: 
    + `204 NO CONTENT`: success response
    + `412 PRECONDITION FAILED`: if the instance you are trying to delete is a related to a protected instance and therefore cannot be deleted.


### Specific ConcreteServer endpoints

#### <a name="Register"></a>Register

- **url**: `auth/register/` 
- **accepts**: `POST` request
- **description**: allows a user to register to the API (see [authentication](authentication.md) section).

#### Login

- **url**: `auth/login/`
- **accepts**: `POST` request
- **description**: allows a user to log in the API (see [authentication](authentication.md) section).

#### Account Me

- **url**: `account/me/` 
- **accepts**: `GET` request
- **description**: allows a user to retrieve its own information on the API
- **request**:

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "http://<webapp>/api/v1.1/account/me/"
```

- **response**: `200 OK` with the JSON containing the user's information.

#### Change Password

- **url**: `auth/change-password/`
- **accepts**: `POST` request
- **description**: allows a user to change a password. Two use cases can be found for this endpoint:
- **request**:

if a user's password has expired, this user will receive a `password_change_token` when attempting to log in the plateform with his expired password. He can use this token to change his own password:

```shell
curl \
  -X POST \
  -H "Authorization: Token <auth_token>" \
  -d '{"email": "<user_email>","password1":"<new_password>","password2":"<new_password>","password_modification_token":"<token_returned_by_login>"}' \
  "http://<webapp>/api/v1.1/auth/change-password/"
```

- **response**: `200 OK` with the JSON containing the user's information.

if a user of a level manager or above wants to change another user's password. Thus, the requester should satisfy either one of these conditions:

-  is superuser
-  is admin and the password that he attempts to changes belongs to a manager or a simple user
-  is manager and he has the same scope that the targeted user (if datamodel is not scoped, no manager can change another user's password)

```shell
curl \
  -X POST \
  -H "Authorization: Token <auth_token>" \
  -d '{"email": "<target_user_email>","password1":"<new_password>","password2":"<new_password>"}' \
  "http://<webapp>/api/v1.1/auth/change-password/"
```

- **response**: `200 OK` with the following JSON:

```json
{
    "email": "<user_email>",
    "message": "Password updated !"
}
```

#### Reset Password

- **url**: `auth/reset-password/` 
- **accepts**: `POST` request
- **description**: allows a user to request a reset of his own password if he has forgotten it (see [authentication](authentication.md) section).

#### Secure Connect

##### Retrieve Token

- **url**: `secure-connect/retrieve-token/`
- **accepts**: `POST` request
- **description**: allows a user to generate a token that will be used for secure login. An email will be sent to the email address containing the login url.
- **request**:

```shell
curl \
  -X POST \
  -d '{"email": "<user_email>"}' \
  "http://<webapp>/api/v1.1/secure-connect/retrieve-token/"
```

- **response**: `201 CREATED` with the following JSON:

```json
{
    "message": "Token created and email sent"
}
```

##### Generate Token

- **url**: `secure-connect/generate-token/`
- **accepts**: `POST` request
- **description**: allows a **superuser** to retrieve a user's token.
- **request**:

```shell
curl \
  -X POST \
  -H "Authorization: Token <auth_token>" \
  -d '{"email": "<target_user_email>"}' \
  "http://<webapp>/api/v1.1/secure-connect/generate-token/"
```

- **response**: `201 CREATED` with the following JSON:

```json
{
    "secure-token":"1023ccc9-d8e8-4eef-86ae-889c37ec96b7"
}
```

##### Login

- **url**: `secure-connect/login/`
- **accepts**: `POST` request
- **description**: allows a user to authenticate to the API using his secure token.
- **request**:

```shell
curl \
  -X POST \
  -d '{"token": "<secure_connect_token>"}' \
  "http://<webapp>/api/v1.1/secure-connect/login/"
```

- **response**: `200 OK` with the JSON containing the user's information.

#### <a name="Blockedusers"></a>Access bloqued users

- **url**: `blocked-users`
- **accepts**: `GET` request
- **description**: allows a user (must be of level `admin` or `superuser`) to retrieve the list of all `blocked` users.
- **request**:

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "http://<webapp>/api/v1.1/blocked-users/"
```

- **response**: `200 OK`:

```json
{
  "objects_count": 4,
  "next": null,
  "previous": null,
  "results": [
    ...
  ],
  "objects_count_per_page": 125,
  "num_total_pages": 1,
  "num_current_page": 1,
  "max_allowed_objects_per_page": 250,
  "model_name": "User",
  "model_verbose_name": "User",
  "list_display": [
    "email",
    "first_name",
    "last_name"
  ],
  "list_filter": {
    "email": "char"
  },
  "total_objects_count": 4,
  "create_url": "http://<webapp>/api/v1.1/auth/register/"
}
```

#### Access a specific bloqued user

- **url**: `blocked-users/<user_uid>`
- **accepts**: `GET` request
- **description**: allows a user (must be of level `admin` or `superuser`) to retrieve a specific `blocked` user. 
- **request**:

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "http://<webapp>/api/v1.1/blocked-users/<user_uid>/"
```

- **response**: `200 OK` with the JSON containing the blocked user's information.

#### Unblock blocked user(s)

- **url**: `unblock-users/`
- **accepts**: `POST` request
- **description**: allows a user (must be of level `admin` or `superuser`) to unblock one or more users. The unblocked users will have a level of `simpleuser`.
- **request**:

```shell
curl \
  -X POST \
  -H "Authorization: Token <auth_token>" \
  -d '{"user_uids": ["<uid1>", "<uid2>"]}' \
  "http://<webapp>/api/v1.1/unblock-users/"
```

- **response**: `200 OK` with the following JSON:

```json
{
    "<uid1>": "User successfully unblocked",
    "<uid2>": "User successfully unblocked"
}
```
