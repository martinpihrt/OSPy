"""OpenAPI description for the stable mobile API."""


def document(server_url="/api/v1"):
    paths = {}

    def add(path, methods, summary, scope=None):
        paths[path] = {}
        for method in methods:
            operation = {
                "summary": summary,
                "responses": {
                    "200": {"description": "Successful response"},
                    "400": {"description": "Invalid request"},
                    "401": {"description": "Authentication required"},
                },
            }
            method_scope = scope.get(method, None) if isinstance(scope, dict) else scope
            if method_scope:
                operation["security"] = [{"bearerAuth": [method_scope]}]
            paths[path][method.lower()] = operation

    add("/", ["GET"], "API identity and version")
    add("/server", ["GET"], "OSPy instance identity")
    add("/capabilities", ["GET"], "Client capability discovery")
    add("/auth/login", ["POST"], "Pair a device and obtain tokens")
    add("/auth/refresh", ["POST"], "Rotate a refresh token")
    add("/auth/logout", ["POST"], "Revoke the current token", "read")
    add("/auth/devices", ["GET"], "List paired devices", "read")
    add("/auth/devices/{device_id}", ["DELETE"], "Revoke a paired device", "read")
    add("/push", ["GET", "POST", "PUT", "DELETE"], "Manage this device push subscription", "read")
    add("/push/test", ["POST"], "Queue a test push notification for this device", "read")
    add("/overview", ["GET"], "Home-screen aggregate", "read")
    add("/irrigation", ["GET", "PUT"], "Read or control global irrigation settings", {
        "GET": "read", "PUT": "control",
    })
    add("/stations", ["GET", "PUT"], "List or configure stations and master outputs", {
        "GET": "read", "PUT": "configuration",
    })
    add("/stations/{station_id}", ["GET", "PUT"], "Read or configure one station", {
        "GET": "read", "PUT": "configuration",
    })
    add("/stations/{station_id}/actions/{action}", ["POST"], "Start or stop a station", "control")
    paths["/stations/{station_id}/actions/{action}"]["post"]["requestBody"] = {
        "required": False,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "duration_seconds": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 59999,
                            "description": "Optional bounded duration for a start action. Omit it to run until stopped.",
                        }
                    },
                    "additionalProperties": False,
                }
            }
        },
    }
    add("/stations/actions/stop-all", ["POST"], "Stop every station and active schedule", "control")
    add("/programs", ["GET", "POST"], "List or create programs", {
        "GET": "read", "POST": "configuration",
    })
    add("/programs/{program_id}", ["GET", "PUT", "DELETE"], "Read, configure or delete a program", {
        "GET": "read", "PUT": "configuration", "DELETE": "configuration",
    })
    add("/programs/{program_id}/actions/{action}", ["POST"], "Run or stop a program", "control")
    add("/program-groups", ["GET"], "List program groups, next runs and active postponements", "read")
    add("/program-groups/{group_id}/postponements", ["POST"], "Postpone the next run of a program group", "control")
    add("/program-groups/{group_id}/postponements/{postponement_id}", ["DELETE"], "Cancel a program group postponement", "control")
    add("/run-once", ["GET", "PUT"], "Read or configure run-once durations", "control")
    add("/run-once/actions/start", ["POST"], "Start run-once irrigation", "control")
    add("/sensors", ["GET"], "List sensors", "read")
    add("/sensors/{sensor_id}", ["GET", "PUT"], "Read or configure one sensor", {
        "GET": "read", "PUT": "configuration",
    })
    add("/sensors/{sensor_id}/history", ["GET"], "Sensor history", "read")
    add("/weather/current", ["GET"], "Current weather", "read")
    add("/weather/forecast", ["GET"], "Weather forecast", "read")
    add("/weather/status", ["GET"], "Weather provider status", "read")
    add("/schedule", ["GET"], "Normalized watering timeline", "read")
    add("/logs/{kind}", ["GET"], "Paginated run, event or e-mail log", "read")
    add("/diagnostics/{section}", ["GET"], "Diagnostics section", "read")
    add("/notifications", ["GET"], "Mobile notifications", "read")
    add("/notifications/{notification_id}/ack", ["POST"], "Acknowledge notification", "read")
    add("/changes", ["GET"], "Replayable incremental changes", "read")
    add("/stream", ["GET"], "Server-sent event stream", "read")
    add("/plugins", ["GET"], "List plug-ins and health", "read")
    add("/plugins/{plugin_id}", ["GET", "PUT"], "Read or enable/disable one plug-in", {
        "GET": "read", "PUT": "plugins",
    })
    add("/plugins/{plugin_id}/mobile", ["GET"], "Plug-in mobile contribution", "read")
    paths["/plugins/{plugin_id}/mobile"]["get"]["parameters"] = [
        {
            "name": "from",
            "in": "query",
            "description": "Inclusive ISO 8601 start of the requested history interval.",
            "required": False,
            "schema": {"type": "string", "format": "date-time"},
        },
        {
            "name": "to",
            "in": "query",
            "description": "Inclusive ISO 8601 end of the requested history interval.",
            "required": False,
            "schema": {"type": "string", "format": "date-time"},
        },
        {
            "name": "max_points",
            "in": "query",
            "description": "Maximum number of returned points per series (20-2000).",
            "required": False,
            "schema": {
                "type": "integer", "minimum": 20, "maximum": 2000,
                "default": 400,
            },
        },
    ]
    add("/plugins/{plugin_id}/actions/{action}", ["POST"], "Declared plug-in mobile action", "plugins")
    add("/backups", ["GET", "POST"], "List or create backups", "backup")
    add("/backups/{backup_id}/download", ["GET"], "Download a backup", "backup")
    add("/backups/{backup_id}/restore", ["POST"], "Stage and restore a backup", "backup")
    add("/updates", ["GET"], "Update status", "read")
    add("/updates/actions/{action}", ["POST"], "Check, apply or roll back an update", "update")
    add("/service-outages", ["GET"], "List service outages", "read")
    add("/system/actions/{action}", ["POST"], "Restart OSPy, reboot or power off", "system")
    add("/operations/{operation_id}", ["GET"], "Long-running operation status", "read")

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "OSPy Mobile API",
            "version": "1.0.0",
            "description": "Stable JSON API for native mobile clients. Existing /api remains supported.",
        },
        "servers": [{"url": server_url}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "OSPy access token",
                }
            }
        },
    }
