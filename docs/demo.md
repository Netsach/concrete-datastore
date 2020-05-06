## Demo

### Datamodel
For this demo, we are using the following datamodel

![datamodel](assets/default-graph.png)

(The full datamodel file can be found [here](datamodel-yml.md))


### Register and Authentication
#### Register a user
To register a new user, perform a `POST` request on `/auth/register` with data containing the fields `email`, `password1`, `password2`:

- **Request**:
```shell
curl \
   -X POST \
   -d "{\"email\":\"johndoe@netsach.com\",\"password1\":\"netsach2020\",\"password2\":\"netsach2020\",\"first_name\":\"John\",\"last_name\":\"Doe\"}" \
   -H "Content-Type: application/json" \
   "https://<webapp>/api/v1.1/auth/register/"
```

- **Response**:
Your user will be created with a level `simpleuser` and with a unique token.

The server will response with the following JSON:
```json
{
  "uid": "fe2ad17a-4678-499c-a957-4cd84dd16e08",
  "email": "johndoe@netsach.com",
  "url": "https://localhost:8000/api/v1.1/account/me/",
  "token": "e72e8df2d1ab9ee0d7cb61367958e4bb8620c1e6",
  "first_name": "John",
  "last_name": "Doe",
  "level": "simpleuser",
  "is_verified": true,
  "groups": [],
  "defaultdividers": []
}
```
The token will be used for further autheticated requests.

#### Login to the API
In order to login to the platform and retrieve your token, you can perform a `POST` request on `/auth/login/` with data containing your user's email and password (used to register):
```shell
curl \
   -X POST \
   -d "{\"email\":\"johndoe@netsach.com\",\"password\":\"netsach2020\"}" \
   -H "Content-Type: application/json" \
   "https://<webapp>/api/v1.1/auth/login/"
```
The server will respond with a JSON containing your token along with other user information:
```json
{
  "uid": "fe2ad17a-4678-499c-a957-4cd84dd16e08",
  "email": "johndoe@netsach.com",
  "url": "https://localhost:8000/api/v1.1/account/me/",
  "token": "e72e8df2d1ab9ee0d7cb61367958e4bb8620c1e6",
  "first_name": "John",
  "last_name": "Doe",
  "level": "simpleuser",
  "is_verified": true,
  "groups": [],
  "defaultdividers": []
}
```

### Perform an authenticated request
Once you have your token, you can create a new instance of the model `Project` (You should have the permissions required to perform the operation, see `permissions` in the datamodel and take a look at the minimum creation level allowed of model Project. Here we have set the `create` permission to authenticated for the sake of the example):

```shell
curl \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Token e72e8df2d1ab9ee0d7cb61367958e4bb8620c1e6" \
    -d '{"name":"MyFirstProject","code":"MFP",manager_uid":"fe2ad17a-4678-499c-a957-4cd84dd16e08","start_date":"2020-01-24T10:23:53Z"}' \
    "https://<webapp>/api/v1.1/project/"
```

The instance is created and the server responds with the following JSON:

```json
{
  "uid": "b1546151-3519-415d-8d8d-8cc113dc1408",
  "name": "MyFirstProject",
  "code": "MFP",
  "manager": "c18f9045-b850-47a5-9d48-5ee2a8196bb8",
  "start_date": "2020-01-24T10:23:53Z",
  "modification_date": "2020-01-24T09:36:24Z",
  "creation_date": "2020-01-24T09:36:24Z",
  "public": false,
  "url": "https://<webapp>/api/v1.1/project/b1546151-3519-415d-8d8d-8cc113dc1408/",
  "verbose_name": "MyFirstProject",
  "created_by": "fe2ad17a-4678-499c-a957-4cd84dd16e08",
  "can_admin_users": [],
  "can_view_users": [],
  "can_admin_groups": [],
  "can_view_groups": [],
  "manager_uid": "c18f9045-b850-47a5-9d48-5ee2a8196bb8"
}
```

You can also list all instances of model `Project` with a `GET` request on `api/v1.1/project/` with your token:
```shell
curl \
    -X GET \
    -H "Authorization: Token e72e8df2d1ab9ee0d7cb61367958e4bb8620c1e6" \
    "https://<webapp>/api/v1.1/project/"
```
The API responds with the following JSON:
```json
{
  "objects_count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "uid": "b1546151-3519-415d-8d8d-8cc113dc1408",
      "name": "MyFirstProject",
      "code": "MFP",
      "manager": "c18f9045-b850-47a5-9d48-5ee2a8196bb8",
      "start_date": "2020-01-24T10:23:53Z",
      "modification_date": "2020-01-24T09:36:24Z",
      "creation_date": "2020-01-24T09:36:24Z",
      "public": false,
      "url": "https://<webapp>/api/v1.1/project/b1546151-3519-415d-8d8d-8cc113dc1408/",
      "verbose_name": "MyFirstProject",
      "created_by": "fe2ad17a-4678-499c-a957-4cd84dd16e08",
      "can_admin_users": [],
      "can_view_users": [],
      "can_admin_groups": [],
      "can_view_groups": [],
      "manager_uid": "c18f9045-b850-47a5-9d48-5ee2a8196bb8"
    }
  ],
  "objects_count_per_page": 125,
  "num_total_pages": 1,
  "num_current_page": 1,
  "max_allowed_objects_per_page": 250,
  "model_name": "Project",
  "model_verbose_name": "Project",
  "list_display": [
    "name",
    "code"
  ],
  "list_filter": {},
  "total_objects_count": 1,
  "create_url": "https://<webapp>/api/v1.1/project/"
}
```
