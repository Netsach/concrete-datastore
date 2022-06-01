# coding: utf-8

# Yaml content that raise a ScannerError
YAML_CONTENT_ERROR = """
a: 1
 b: 2
"""

YAML_CONTENT_UNKNOWN_IP_PROTOCOL = """manifest:
  version: 1.0.0
  attributes: []
  data_modeling:
    roles: []
    models:
      - fields:
          - attributes:
              to:
                uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
                name: User
              reverse: concrete_groups
            datatype: m2m
            name: members
          - attributes: {}
            datatype: char
            name: name
        name: Group
        uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        description: null
        representation_field: name
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: email
          - attributes: {}
            datatype: char
            name: first_name
          - attributes: {}
            datatype: char
            name: last_name
          - attributes:
              protocol: ipv42
            datatype: ip
            name: multicast_ip
        name: User
        uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        description: null
        representation_field: email
        is_default_public: false
    version: 1.0.0
    attributes: []
    permissions:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        lookups: []
        minimum_levels:
          create: manager
          delete: admin
          update: manager
          retrieve: authenticated
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        model_name: User
        lookups: []
        minimum_levels:
          create: manager
          delete: manager
          update: authenticated
          retrieve: authenticated
    application_id: ""
    resource_queries:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        search_fields:
          - name
        filter_fields:
          - name
        display_fields:
          - name
        export_fields: []
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
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
    one_to_many_relations: []
    many_to_many_relations:
      - source_field: members
        source_model:
          uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
          name: Group
        target_model:
          uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
          name: User
"""

YAML_CONTENT_DUPLICATE_RELATION = """manifest:
  version: 1.0.0
  attributes: []
  data_modeling:
    roles: []
    models:
      - fields:
          - attributes:
              to:
                uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
                name: User
              reverse: concrete_groups
            datatype: m2m
            name: members
          - attributes: {}
            datatype: char
            name: name
        name: Group
        uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        description: null
        representation_field: name
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: email
          - attributes: {}
            datatype: char
            name: first_name
          - attributes: {}
            datatype: char
            name: last_name
          - attributes:
              protocol: ipv4
            datatype: ip
            name: multicast_ip
        name: User
        uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        description: null
        representation_field: email
        is_default_public: false
    version: 1.0.0
    attributes: []
    permissions:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        lookups: []
        minimum_levels:
          create: manager
          delete: admin
          update: manager
          retrieve: authenticated
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        model_name: User
        lookups: []
        minimum_levels:
          create: manager
          delete: manager
          update: authenticated
          retrieve: authenticated
    application_id: ""
    resource_queries:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        search_fields:
          - name
        filter_fields:
          - name
        display_fields:
          - name
        export_fields: []
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
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
    one_to_many_relations: []
    many_to_many_relations:
      - source_field: members
        source_model:
          uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
          name: Group
        target_model:
          uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
          name: User
      - source_field: members
        source_model:
          uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
          name: Group
        target_model:
          uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
          name: User
"""

# Missing permissions for model User
YAML_CONTENT_MISSING_PERMISSIONS = """manifest:
  version: 1.0.0
  attributes: []
  data_modeling:
    roles: []
    models:
      - fields:
          - attributes:
              to:
                uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
                name: User
              reverse: concrete_groups
            datatype: m2m
            name: members
          - attributes: {}
            datatype: char
            name: name
        name: Group
        uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        description: null
        representation_field: name
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: email
          - attributes: {}
            datatype: char
            name: first_name
          - attributes: {}
            datatype: char
            name: last_name
          - attributes:
              protocol: ipv4
            datatype: ip
            name: multicast_ip
        name: User
        uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        description: null
        representation_field: email
        is_default_public: false
    version: 1.0.0
    attributes: []
    permissions:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        lookups: []
        minimum_levels:
          create: manager
          delete: admin
          update: manager
          retrieve: authenticated
    application_id: ""
    resource_queries:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        search_fields:
          - name
        filter_fields:
          - name
        display_fields:
          - name
        export_fields: []
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
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
    one_to_many_relations: []
    many_to_many_relations:
      - source_field: members
        source_model:
          uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
          name: Group
        target_model:
          uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
          name: User
"""

# Duplicate of permissions for model User
YAML_CONTENT_DUPLICATE_PERMISSIONS = """manifest:
  version: 1.0.0
  attributes: []
  data_modeling:
    roles: []
    models:
      - fields:
          - attributes:
              to:
                uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
                name: User
              reverse: concrete_groups
            datatype: m2m
            name: members
          - attributes: {}
            datatype: char
            name: name
        name: Group
        uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        description: null
        representation_field: name
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: email
          - attributes: {}
            datatype: char
            name: first_name
          - attributes: {}
            datatype: char
            name: last_name
          - attributes:
              protocol: ipv4
            datatype: ip
            name: multicast_ip
        name: User
        uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        description: null
        representation_field: email
        is_default_public: false
    version: 1.0.0
    attributes: []
    permissions:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        lookups: []
        minimum_levels:
          create: manager
          delete: admin
          update: manager
          retrieve: authenticated
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        model_name: User
        lookups: []
        minimum_levels:
          create: manager
          delete: manager
          update: authenticated
          retrieve: authenticated
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        model_name: User
        lookups: []
        minimum_levels:
          create: manager
          delete: manager
          update: authenticated
          retrieve: authenticated
    application_id: ""
    resource_queries:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        search_fields:
          - name
        filter_fields:
          - name
        display_fields:
          - name
        export_fields: []
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
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
    one_to_many_relations: []
    many_to_many_relations:
      - source_field: members
        source_model:
          uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
          name: Group
        target_model:
          uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
          name: User
"""


# Name of a field not allowed (break)
YAML_CONTENT_NAME_NOT_ALLOWED = """manifest:
  version: 1.0.0
  attributes: []
  data_modeling:
    roles: []
    models:
      - fields:
          - attributes:
              to:
                uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
                name: User
              reverse: concrete_groups
            datatype: m2m
            name: members
          - attributes: {}
            datatype: char
            name: name
        name: Group
        uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        description: null
        representation_field: name
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: email
          - attributes: {}
            datatype: char
            name: first_name
          - attributes: {}
            datatype: char
            name: last_name
          - attributes:
              protocol: ipv4
            datatype: ip
            name: break
        name: User
        uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        description: null
        representation_field: email
        is_default_public: false
    version: 1.0.0
    attributes: []
    permissions:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        lookups: []
        minimum_levels:
          create: manager
          delete: admin
          update: manager
          retrieve: authenticated
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        model_name: User
        lookups: []
        minimum_levels:
          create: manager
          delete: manager
          update: authenticated
          retrieve: authenticated
    application_id: ""
    resource_queries:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        search_fields:
          - name
        filter_fields:
          - name
        display_fields:
          - name
        export_fields: []
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
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
    one_to_many_relations: []
    many_to_many_relations:
      - source_field: members
        source_model:
          uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
          name: Group
        target_model:
          uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
          name: User
"""


# Duplicate of permissions for model User
YAML_CONTENT_DUPLICATE_FIELD = """manifest:
  version: 1.0.0
  attributes: []
  data_modeling:
    roles: []
    models:
      - fields:
          - attributes:
              to:
                uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
                name: User
              reverse: concrete_groups
            datatype: m2m
            name: members
          - attributes: {}
            datatype: char
            name: name
        name: Group
        uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        description: null
        representation_field: name
        is_default_public: false
      - fields:
          - attributes: {}
            datatype: char
            name: email
          - attributes: {}
            datatype: char
            name: first_name
          - attributes: {}
            datatype: char
            name: last_name
          - attributes:
              protocol: ipv4
            datatype: ip
            name: multicast_ip
          - attributes:
              protocol: ipv4
            datatype: ip
            name: multicast_ip
        name: User
        uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        description: null
        representation_field: email
        is_default_public: false
    version: 1.0.0
    attributes: []
    permissions:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        lookups: []
        minimum_levels:
          create: manager
          delete: admin
          update: manager
          retrieve: authenticated
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
        model_name: User
        lookups: []
        minimum_levels:
          create: manager
          delete: manager
          update: authenticated
          retrieve: authenticated
    application_id: ""
    resource_queries:
      - model_uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
        model_name: Group
        search_fields:
          - name
        filter_fields:
          - name
        display_fields:
          - name
        export_fields: []
      - model_uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
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
    one_to_many_relations: []
    many_to_many_relations:
      - source_field: members
        source_model:
          uid: 3db6598f-cdba-49ba-b0de-b1852b8b5e15
          name: Group
        target_model:
          uid: 30c61a83-aa4c-4f20-b225-a9634f8170d1
          name: User
"""
