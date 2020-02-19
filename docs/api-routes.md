## API routes, methods and responses

For all the routes listed below, the API response has the following **failure status codes**:

- `401 UNAUTHORIZED`: if the user has not the rigths to access the data.
- `403 FORBIDDEN`: if the user is not authenticated to the API.
- `404 NOT FOUND`: if the url is not found.

### Models related API endpoints

As explained in the introduction, Concrete Datastore consumes a datamodel definition in order to generate an API giving acess to the instances of the datastore. For each model, Concrete Datastore generates andpoints that allow a user to perform **CRUD** methods. this endpoint is a `kebab-case` (lower case with hyphens) of the model's name. For example if you have a model named `MyModel`, the API endpoint will be `my-model`.

For each model, Concrete Datastore exposes two routes accepting different methods:

#### List all instances of model MyModel

A `GET` on the root url of the model MyModel will retrieve all instances of this model.

- **Method** : `GET`

- **Endpoint**: `https://<webapp>/api/v1.1/my-model/`

- **Example** :

**Request** 

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "https://<webapp>/api/v1.1/my-model/"
```

**Response** with status code HTTP `200 (OK)`, the response body is a JSON containing the details of all instances available. The response is paginated.

```json
{
  "objects_count": 125,
  "next": "https://<webapp>/api/v1.1/my-model/?page=2",
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
  "create_url": "https://<webapp>/api/v1.1/my-model/"
}
```

- **Response format** :

The JSON response contains the following keys:

- `objects_count`: number of objects found in this current page
- `next`: URL to the next page (null if the current page is the last/only page)
- `previous`: URL to the previous page (null if the current page is the first/only page)
- `results`: list of all the instances
- `objects_count_per_page`: pagination of the response
- `num_total_pages`: number of total pages
- `num_current_page`: index of the current page
- `max_allowed_objects_per_page`: max instances to be displayed in one response
- `model_name`: model name
- `model_verbose_name`: model verbose name
- `list_display`: list of displayed fields (defined in the datamodel)
- `list_filter`: mapping of the filter fields with `{field_name: field_type}`. Filter fields are defined in the datamodel
- `total_objects_count`: total instances of the current model
- `create_url`: url for instance creation (with a `POST` request)

**IMPORTANT:** For model **User**, the list won't contain any user with the level `blocked`. In order to access these users, see [blocked users](#Blockedusers)

#### Create a new instance of model MyModel

A `POST` on the root url of the model MyModel will create a new instance of this model.

- **Method** : `POST`

- **Endpoint**: `https://<webapp>/api/v1.1/my-model/`

- **Example** :

**Request**

```shell
curl \
    -X POST \
    -H "Authorization: Token <auth_token>" \
    -d "<JSON data for the new instance to create>" \
    "https://<webapp>/api/v1.1/my-model/"
```

**Responses** with status code HTTP  `201 (CREATED)`, the response body is a JSON containing the fields of the new instance created.

**IMPORTANT:** For model **User**, `POST` request is not allowed. In order to create a new user, you should perform a [register](#Register)

#### Retrieve a specific instance of model MyModel by its UID

A `GET` on the url of a given instance of model MyModel will retrieve the fields of this given instance.

- **Method** : `GET`

- **Endpoint**: `https://<webapp>/api/v1.1/my-model/<uid>/`

- **Example** :

**Request**

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "https://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

**Response** : with status code HTTP `200 (OK)`, the response body is a JSON containing the fields of the instance requested.

#### Update a specific instance of model MyModel by its UID

#### Update some of the fields with `PATCH`

A `PATCH` on the url of a given instance of model MyModel will update the fields of this given instance.

- **Method** : `PATCH`

- **Endpoint**: `https://<webapp>/api/v1.1/my-model/<uid>/`

- **Example** :

**Request**

```shell
curl \
  -X PATCH \
  -H "Authorization: Token <auth_token>" \
  -d "<JSON data to update>" \
  "https://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

**Response** : with status code HTTP `200 (OK)`, the response body is a JSON containing all the fields of the given instance, updated.

#### Update all the fields with `PUT`

A `PUT` on the url of a given instance of model MyModel will update the fields of this given instance.

- **Method** : `PUT`

- **Endpoint**: `https://<webapp>/api/v1.1/my-model/<uid>/`

- **Example** :

**Request**

```shell
curl \
  -X PUT \
  -H "Authorization: Token <auth_token>" \
  -d "<JSON data to update>" \
  "https://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

**Response** : with status code HTTP `200 (OK)`, the response body is a JSON containing all the fields of the given instance, updated.

#### Delete a specific instance of model MyModel by its UID

A `DELETE` on the url of a given instance of model MyModel will retrieve the fields of this given instance.

- **Method** : `DELETE`

- **Endpoint**: `https://<webapp>/api/v1.1/my-model/<uid>/`

- **Example** :

**Request**

```shell
curl \
  -X DELETE \
  -H "Authorization: Token <auth_token>" \
  "https://<webapp>/api/v1.1/my-model/ef29364d-50f6-4e3e-a401-d30fecacf59b/"
```

**Response** : with status code HTTP `204 (NO CONTENT)`, the response body is empty.

This operation could fail, if the instance is a related to a protected instance, it cannot be deleted. In this case, the status code HTTP is `412 (PRECONDITION FAILED)`.


### Specific API endpoints

#### <a name="Register"></a>Register

- **Url** : `auth/register/` 
- **Method** : `POST`
- **Description** : allows a user to register to the API (see [authentication](authentication.md) section).

#### Login

- **Url** : `auth/login/`
- **Method** : `POST`
- **Description** : allows a user to log in the API (see [authentication](authentication.md) section).

#### Account Me

- **Url** : `account/me/` 
- **Method** : `GET`
- **Description** : allows a user to retrieve its own information on the API

**Request** :

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "https://<webapp>/api/v1.1/account/me/"
```

**Response** : `200 OK` with the JSON containing the user's information.

#### Change Password

- **Url** : `auth/change-password/`
- **Method** : `POST`
- **Description** : allows a user to change a password.

**Request** : Two use cases can be found for this endpoint:

if a user's password has expired, this user will receive a `password_change_token` when attempting to log in the plateform with his expired password. He can use this token to change his own password:

```shell
curl \
  -X POST \
  -d '{"email": "<user_email>","password1":"<new_password>","password2":"<new_password>","password_modification_token":"<token_returned_by_login>"}' \
  "https://<webapp>/api/v1.1/auth/change-password/"
```

**Response** : `200 OK` with the JSON containing the user's information.

if a user of a level manager or above wants to change another user's password. Thus, the requester should satisfy either one of these conditions:

-  is superuser
-  is admin and the password that he attempts to changes belongs to a manager or a simple user
-  is manager and he has the same scope that the targeted user (if datamodel is not scoped, no manager can change another user's password)

```shell
curl \
  -X POST \
  -H "Authorization: Token <auth_token>" \
  -d '{"email": "<target_user_email>","password1":"<new_password>","password2":"<new_password>"}' \
  "https://<webapp>/api/v1.1/auth/change-password/"
```

**Response** : `200 OK` with the following JSON:

```json
{
    "email": "<user_email>",
    "message": "Password updated !"
}
```

#### Reset Password

- **Url** : `auth/reset-password/` 
- **Method** : `POST`
- **Description** : allows a user to request a reset of his own password if he has forgotten it (see [authentication](authentication.md) section).

#### Secure Connect

##### Retrieve Token

- **Url** : `secure-connect/retrieve-token/`
- **Method** : `POST`
- **Description** : allows a user to generate a token that will be used for secure login. An email will be sent to the email address containing the login url.
**Request** :

```shell
curl \
  -X POST \
  -d '{"email": "<user_email>"}' \
  "https://<webapp>/api/v1.1/secure-connect/retrieve-token/"
```

**Response** : `201 CREATED` with the following JSON:

```json
{
    "message": "Token created and email sent"
}
```

##### Generate Token

- **Url** : `secure-connect/generate-token/`
- **Method** : `POST`
- **Description** : allows a **superuser** to retrieve a user's token.
**Request** :

```shell
curl \
  -X POST \
  -H "Authorization: Token <auth_token>" \
  -d '{"email": "<target_user_email>"}' \
  "https://<webapp>/api/v1.1/secure-connect/generate-token/"
```

**Response** : `201 CREATED` with the following JSON:

```json
{
    "secure-token":"1023ccc9-d8e8-4eef-86ae-889c37ec96b7"
}
```

##### Login

- **Url** : `secure-connect/login/`
- **Method** : `POST`
- **Description** : allows a user to authenticate to the API using his secure token.
**Request** :

```shell
curl \
  -X POST \
  -d '{"token": "<secure_connect_token>"}' \
  "https://<webapp>/api/v1.1/secure-connect/login/"
```

**Response** : `200 OK` with the JSON containing the user's information.

#### <a name="Blockedusers"></a>Access bloqued users

- **Url** : `blocked-users`
- **Method** : `GET`
- **Description** : allows a user (must be of level `admin` or `superuser`) to retrieve the list of all `blocked` users.
**Request** :

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "https://<webapp>/api/v1.1/blocked-users/"
```

**Response** : `200 OK`:

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
  "create_url": "https://<webapp>/api/v1.1/auth/register/"
}
```

#### Access a specific bloqued user

- **Url** : `blocked-users/<user_uid>`
- **Method** : `GET`
- **Description** : allows a user (must be of level `admin` or `superuser`) to retrieve a specific `blocked` user. 
**Request** :

```shell
curl \
  -H "Authorization: Token <auth_token>" \
  "https://<webapp>/api/v1.1/blocked-users/<user_uid>/"
```

**Response** : `200 OK` with the JSON containing the blocked user's information.

#### Unblock blocked user(s)

- **Url** : `unblock-users/`
- **Method** : `POST`
- **Description** : allows a user (must be of level `admin` or `superuser`) to unblock one or more users. The unblocked users will have a level of `simpleuser`.
**Request** :

```shell
curl \
  -X POST \
  -H "Authorization: Token <auth_token>" \
  -d '{"user_uids": ["<uid1>", "<uid2>"]}' \
  "https://<webapp>/api/v1.1/unblock-users/"
```

**Response** : `200 OK` with the following JSON:

```json
{
    "<uid1>": "User successfully unblocked",
    "<uid2>": "User successfully unblocked"
}
```
