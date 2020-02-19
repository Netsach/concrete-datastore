## Filters and ordering

### Filters
API requests support different types of filters:

- **Filter Supporting Or operation:** by adding the `__in` suffix:
example: `?name__in=project1,project2,project3` returns all objects that the field name has a value of "project1" **OR** "project2" **OR** "project3"
- **Filter Supporting Empty values:** by adding `__isempty=true`:
example: `?project__isempty=true` returns all objects that do not have a `project`
- **Filter Supporting Comparison operations:** by adding the suffixes `__gte`, `__gt`, `__lte` and `__lt`
example:
 * `?price__gte=10` (price >= 10)
 * `?price__gt=10` (price > 10)
 * `?price__lte=10` (price <= 10)
 * `?price__lt=10` (price < 10)
- **Filter Supporting Range:** by adding the suffix `__range`:
example: `?creation_date__range=2018-01-01,2018-12-31` returns all objects with creation date is between 1st Jan 2018 and 31st Dec 2018

- `c_resp_page_size`: The API also features pagination by the use of the query parameter `c_resp_page_size` that takes an integer representing the number of results per page that sould be returned
- `c_resp_nested`: If there are relation between objects, by default the API shows the relation completely, it is nested.
example:

```json
{
      "global_status": "PENDING",
      "name": "Test Name",
      "other_object": { //Nested here
        "status":"other_object_status",
        "name": "other_object_name"
      }
}
```

You can prevent this behavior by filtering with the query parameter `?c_resp_nested=False`

This will only give you the object uid:


```json
{
      "global_status": "PENDING",
      "name": "Test Name",
      "other_object": "b1d30fb2-4d11-4bef-a777-721df8dfe984"
}
```

* **Filter within timestamp range:** You can filter results within timestamp range by adding query parameter `timestamp_start` and `timestamp_end`
examples:
    - `?timestamp_start=100000&timestamp_end=20000`: Filter objects between timestamp [10000, 20000]
    - `?timestamp_start=10000`: Filter objects between timestamp [10000, now]
    - `?timestamp_end=20000`: Filter objects between timestamp [0, 20000]


* **Filter users by level:** You can filter users by level with two filters: `level` and `atleast`
    * **/user/?level**=[user_level]: Users with an exact level `user_level`. The user_level must be in [**superuser**, **admin**, **manager**, **simpleuser**]
    * **/user/?atleast**=[user_level]: Users with a level atleast equal to `user_level`. The user_level must be in [**superuser**, **admin**, **manager**, **simpleuser**]

    Example: `/user/?atleast=manager` gives users with level manager, admin and superuser



**Filter examples**:

```
https://<webapp>/api/v1.1/mymodel/?name=test
https://<webapp>/api/v1.1/mymodel/?name__isempty=true
https://<webapp>/api/v1.1/mymodel/?name__in=project1,project2,project3
https://<webapp>/api/v1.1/mymodel/?price__gte=price
https://<webapp>/api/v1.1/mymodel/?creation_date__range=date1,date2
```


### Ordering
API `GET` requests support ordering on fields in the model's `list_display`.  
In order to get a sorted result from the api, you can use the query parameter `?ordering=<field_name>` (for ascending results) or `?ordering=-<field_name>` (for descending results).

**Examples**:
```
https://<webapp>/api/v1.1/mymodel/?ordering=name
https://<webapp>/api/v1.1/mymodel/?ordering=-name
```
