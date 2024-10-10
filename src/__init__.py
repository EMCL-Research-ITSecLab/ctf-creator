CONFIG_SCHEMA = {
    "name": {"required": True, "type": "string"},
    "containers": {"required": True, "type": "list"},
    "users": {"required": True, "type": "list"},
    "identityFile": {"required": True, "type": "list"},
    "hosts": {"required": True, "type": "list"},
    "metrics": {
        "required": True,
        "type": "dict",
        "schema": {
            "percentage": {
                "required": True,
                "type": "dict",
                "schema": {
                    "value": {"required": True, "type": "number", "min": 0, "max": 100},
                    "trend": {
                        "type": "string",
                        "nullable": True,
                        "regex": "^(?i)(down|equal|up)$",
                    },
                },
            }
        },
    },
}
