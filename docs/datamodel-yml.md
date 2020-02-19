```yml
manifest:
  version: 1.0.0
  attributes: []
  data_modeling:
    roles: []
    models:
      - fields:
          - attributes: {}
            datatype: char
            name: email
            allow_empty: null
          - attributes: {}
            datatype: char
            name: first_name
            allow_empty: null
          - attributes: {}
            datatype: char
            name: last_name
            allow_empty: null
        name: User
        uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
        description: null
        representation_field: email
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: name
            allow_empty: null
          - attributes:
              to:
                uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
                name: User
              reverse: concrete_groups
            datatype: m2m
            name: members
            allow_empty: null
        name: Group
        uid: 87a72328-6efc-49d6-9941-d46042c080fd
        description: null
        representation_field: name
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: name
          - attributes:
              allow_empty: true
            datatype: char
            name: code
          - attributes: {}
            datatype: date
            name: start_date
          - attributes: {}
            datatype: txt
            name: description
          - attributes:
              reverse: owned_projects
              to:
                uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
                name: User
            datatype: fk
            name: manager
          - attributes:
              reverse: projects
              to:
                uid: 87a72328-6efc-49d6-9941-d46042c080fd
                name: Group
              allow_empty: true
            datatype: m2m
            name: groups
        name: Project
        uid: 9a820c34-d618-48cb-b08d-0dc37a3ca26a
        description: null
        representation_field: name
        is_default_public: false
    version: 1.0.0
    attributes: []
    permissions:
      - model_uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
        model_name: User
        lookups: []
        minimum_levels:
          create: manager
          delete: manager
          update: authenticated
          retrieve: authenticated
      - model_uid: 87a72328-6efc-49d6-9941-d46042c080fd
        model_name: Group
        lookups: []
        minimum_levels:
          create: manager
          delete: admin
          update: manager
          retrieve: authenticated
      - model_uid: 9a820c34-d618-48cb-b08d-0dc37a3ca26a
        model_name: Project
        lookups: []
        minimum_levels:
          create: autheticated
          retrieve: autheticated
          update: autheticated
          delete: autheticated
    application_id: ""
    resource_queries:
      - model_uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
        model_name: User
        search_fields:
          - email
        filter_fields:
          - email
        display_fields:
          - email
          - first_name
          - last_name
        export_fields: []
      - model_uid: 87a72328-6efc-49d6-9941-d46042c080fd
        model_name: Group
        search_fields:
          - name
        filter_fields:
          - name
        display_fields:
          - name
        export_fields: []
      - model_uid: 9a820c34-d618-48cb-b08d-0dc37a3ca26a
        model_name: Project
        search_fields: []
        filter_fields: []
        display_fields: []
        export_fields: []
    one_to_one_relations: []
    one_to_many_relations:
      - source_field: manager
        source_model:
          uid: 9a820c34-d618-48cb-b08d-0dc37a3ca26a
          name: Project
        target_model:
          uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
          name: User
      - source_field: manager
        source_model:
          uid: 9a820c34-d618-48cb-b08d-0dc37a3ca26a
          name: Project
        target_model:
          uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
          name: User
    many_to_many_relations:
      - source_field: members
        source_model:
          uid: 87a72328-6efc-49d6-9941-d46042c080fd
          name: Group
        target_model:
          uid: 8dde7da5-3a0a-42a7-b579-390cd686b3fd
          name: User
      - source_field: groups
        source_model:
          uid: 9a820c34-d618-48cb-b08d-0dc37a3ca26a
          name: Project
        target_model:
          uid: 87a72328-6efc-49d6-9941-d46042c080fd
          name: Group
```
You can download the datamodel file [here](assets/sample-datamodel.yml)
