## Filters and ordering

### Filters
API requests support different types of filters on the fields of the `filter_fields` declared in the datamodel, and other specific query parameters:

#### Filter against model fields

- **Filter exact value:** (Applied on all fields within the `filter_fields` except for JsonFields and PointFields) by using a strict equality (`field_name=field_value`) and returns all instances that have `field_value` as a value for `field_name`. This allows also an exclude filter by adding a negation mark (`!`) after the query param, in order to exclude the instances that match the filter (`field_name!=field_value`)
- **Filter Supporting Or operation:** (Applied on all fields within the `filter_fields`) By adding the `__in` suffix:
example: `?name__in=project1,project2,project3` returns all objects that the field name has a value of "project1" **OR** "project2" **OR** "project3". This allows also an exclude filter by adding a negation mark (`!`) after the query param, in order to exclude the instances that match the filter. Example: `?name__in!=project1,project2,project3` returns all objects that the field name is **NEITHER** "project1" **NOR** "project2" **NOR** "project3"
- **Filter Supporting Contains key:** (Applied on CharFields and TextFields) By adding the `__contains` suffix:
example: `?name__contains=pro` returns all objects that the field name contains the substring `"pro"`. This allows also an exclude filter by adding a negation mark (`!`) after the query param, in order to exclude the instances that match the filter. Exmple: `?name__contains!=pro` returns all objects that the field name does not contain the substring `"pro"`. Please note that the `__contains` filter is case-sensitive. For case-insensitive filter, you can use the lookup `__icontains`.
- **Filter Supporting Empty values:** (Applied on the CharFields and TextFields) By adding `__isempty=true` or `is__empty=false`:
example: `?name__isempty=true` returns all objects that do not have a `name` and `?name__isempty=false` returns all objects have a non empty `name`
- **Filter Supporting Null Relation:** (Applied on the ForeignKeys and ManyToManyField) By adding `__isnull=true`:
example: `?project__isnull=true` returns all objects that do not have a `project`
- **Filter Supporting Comparison operations:** (Applied on DateTimeFields, DateFields, DecimalFields, IntegerFields and FloatFields) By adding the lookups `__gte`, `__gt`, `__lte` or `__lt`.
example:
    - `?price__gte=10` (price >= 10)
    - `?price__gt=10` (price > 10)
    - `?price__lte=10` (price <= 10)
    - `?price__lt=10` (price < 10)

- **Filters Supporting Distance:** (Applied only on PointFields) By adding the lookups `__distance_gte`, `__distance_gt`, `__distance_lte`, `__distance_lt`, `__distance_range` or `__distance_range!`.
    - `?coords__distance_gte=30,1.34,48.543` the distance from the point with longitude 1.34 and latitude 48.543 is bigger or equal to 30 meters
    - `?coords__distance_gt=30,1.34,48.543` the distance from the point with longitude 1.34 and latitude 48.543 is strictly bigger than 30 meters
    - `?coords__distance_lte=30,1.34,48.543` the distance from the point with longitude 1.34 and latitude 48.543 is less or equal to 30 meters
    - `?coords__distance_lt=30,1.34,48.543` the distance from the point with longitude 1.34 and latitude 48.543 is strictly less than 30 meters
    - `?coords__distance_range=30,40,1.34,48.543` the distance from the point with longitude 1.34 and latitude 48.543 is between 30 meters and 40 meters (inclusive range)
    - `?coords__distance_range!=30,1.34,48.543` the distance from the point with longitude 1.34 and latitude 48.543 is either strictly bigger than 40 meters or strictly less than 30 meters.
- **Filter Supporting Range:** (Applied on DateTimeFields, DateFields, DecimalFields, IntegerFields and FloatFields) By adding the suffix `__range`: example: `?creation_date__range=2018-01-01,2018-12-31` returns all objects with creation date is between 1st Jan 2018 and 31st Dec 2018 (inclusive range). This allows also an exclude filter by adding a negation mark (`!`) after the query param, in order to exclude the instances that match the filter. Exmple: `?creation_date__range!=2018-01-01,2018-12-31` return all the objects that were created **EITHER** before 1st Jan 2018 **OR** after 31st Dec 2018

**Examples**:

```
https://<webapp>/api/v1.1/mymodel/?name=test
https://<webapp>/api/v1.1/mymodel/?name!=test
https://<webapp>/api/v1.1/mymodel/?name__isempty=true
https://<webapp>/api/v1.1/mymodel/?name__isempty=false
https://<webapp>/api/v1.1/mymodel/?name__in=project1,project2,project3
https://<webapp>/api/v1.1/mymodel/?name__in!=project1,project2,project3
https://<webapp>/api/v1.1/mymodel/?price__gte=price
https://<webapp>/api/v1.1/mymodel/?creation_date__range=date1,date2
https://<webapp>/api/v1.1/mymodel/?creation_date__range!=date1,date2
https://<webapp>/api/v1.1/mymodel/?coords__lte=Distance,Longitude,latitude
https://<webapp>/api/v1.1/mymodel/?coords__range=Distance1,Distance2,Longitude,latitude
```


#### Filter using specific query parameters

- `c_resp_page_size`: The API also features pagination by the use of the query parameter `c_resp_page_size` that takes an integer representing the number of results per page that sould be returned
- `c_resp_nested`: If there are relation between objects, by default the API shows the relation completely, it is nested.
Example:

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
    - `?timestamp_start=100000&timestamp_end=20000`: Filter objects between timestamp [10000, 20000] based on the **modification_date**.
    - `?timestamp_start=10000`: Filter objects between timestamp [10000, now] based on the **modification_date**.
    - `?timestamp_end=20000`: Filter objects between timestamp [0, 20000] based on the **modification_date**.
    
    
    
If `timestamp_start` is specified and `> 0`, the api reponse will contain the following additionnal elements:
    - `"timestamp_start"`: the given timestamp start
    - `"timestamp_end"`: the timestamp end if given in the queryparams, otherwise the current timestamp
    - `"deleted_uids"`: a list of the objects' uids that are now longer in the response. Please refer to [the example on how to properly use timestamp_start and timestamp_end](#TimestampStartEnd)

<a name="TimestampStartEnd"></a>**Using timestamp_start and timestamp_end examples**:

Given a model `Article` with a float field `price`.
Given two instances of this model:

-  article1 (price=53.99)
-  article2 (price=52.99)

To retrieve all articles with a price greater than or equal to 50.00:
```
https://<webapp>/api/v1.1/article/?price__gte=50.0&timestamp_start=0
```

The API response is:

```json
{
  "objects_count": 2,
  "next": null,
  "previous": null,
  "results": [ // both articles are in the reponse
    // article1,
    // article2
  ],
  "objects_count_per_page": 250,
  "num_total_pages": 1,
  "num_current_page": 1,
  "max_allowed_objects_per_page": 250,
  "model_name": "Article",
  "model_verbose_name": "Article",
  "list_display": [],
  "list_filter": {},
  "total_objects_count": 2,
  "create_url": "https://<webapp>/api/v1.1/article/",
  "timestamp_start": 0.0,
  "timestamp_end": 1603716926.382462,
  "deleted_uids": []
}
```

If you use the returned `timestamp_end` to perform the GET request:
```
https://<webapp>/api/v1.1/article/?price__gte=50.0&timestamp_start=1603716926.382462
```

then the results will be an empty list, because between `1603716926.382462` and the current timestamp, nothing changed in the Database
```json
{
  "objects_count": 0,
  "next": null,
  "previous": null,
  "results": [], // no articles in the reponse
  "objects_count_per_page": 250,
  "num_total_pages": 1,
  "num_current_page": 1,
  "max_allowed_objects_per_page": 250,
  "model_name": "Article",
  "model_verbose_name": "Article",
  "list_display": [],
  "list_filter": {},
  "total_objects_count": 0,
  "create_url": "https://<webapp>/api/v1.1/article/",
  "timestamp_start": 1603716926.382462,
  "timestamp_end": 1603716951.567238,
  "deleted_uids": []
}
```

Now, if you add a new instance to the model `Article`: article3 (price=55.00) and perform the get request with the same filters, using the last timestamp_end as the new timestamp_start:
```
https://<webapp>/api/v1.1/article/?price__gte=50.0&timestamp_start=1603716951.567238
```

the results will contain only `article3`:

```json
{
  "objects_count": 1,
  "next": null,
  "previous": null,
  "results": [ // only the 3rd article
    // article3
  ],
  "objects_count_per_page": 250,
  "num_total_pages": 1,
  "num_current_page": 1,
  "max_allowed_objects_per_page": 250,
  "model_name": "Article",
  "model_verbose_name": "Article",
  "list_display": [],
  "list_filter": {},
  "total_objects_count": 1,
  "create_url": "https://<webapp>/api/v1.1/article/",
  "timestamp_start": 1603716951.567238,
  "timestamp_end": 1603717103.926404,
  "deleted_uids": []
}
```

If you update article1 with `price = 49.99` and perform the request with the filter `?price__gte=50.0` and the timstamp_start to `1603717103.926404`, article1's uid will appear in the deleted uids, because it no longer satisfies the filters:

```
https://<webapp>/api/v1.1/article/?price__gte=50.0&timestamp_start=1603717103.926404
```

```json
{
  "objects_count": 0,
  "next": null,
  "previous": null,
  "results": [], // no articles in the reponse
  "objects_count_per_page": 250,
  "num_total_pages": 1,
  "num_current_page": 1,
  "max_allowed_objects_per_page": 250,
  "model_name": "Article",
  "model_verbose_name": "Article",
  "list_display": [],
  "list_filter": {},
  "total_objects_count": 0,
  "create_url": "https://<webapp>/api/v1.1/article/",
  "timestamp_start": 1603717103.926404,
  "timestamp_end": 1603717216.513412,
  "deleted_uids": [
    "1d80d208-1748-4784-a9e6-f0f70a2ecc64" // article1's uid
  ]
}
```

### Additional filters for User model

* **Filter users by level:** You can filter users by level with two filters: `level` and `atleast`
    - `/user/?level=<user_level>`: Users with an exact level `user_level`. The user_level must be in [**superuser**, **admin**, **manager**, **simpleuser**]
    - `/user/?atleast=<user_level>`: Users with a level atleast equal to `user_level`. The user_level must be in [**superuser**, **admin**, **manager**, **simpleuser**]

    Example: `/user/?atleast=manager` returns users with level manager, admin and superuser


### Ordering
API `GET` requests support ordering on fields in the model's `ordering_fields`.  
In order to get a sorted result from the api, you can use the query parameter `?ordering=<field_name>` (for ascending results) or `?ordering=-<field_name>` (for descending results).

**Examples**:
```
https://<webapp>/api/v1.1/mymodel/?ordering=name
https://<webapp>/api/v1.1/mymodel/?ordering=-name
```
