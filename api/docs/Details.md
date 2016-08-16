API Details
====

### HTTP Method Mapping
|Method|Mapping|
|:--|:--|
GET|Get / List object/s
PUT|Update / modify object/s
POST|Create new object/s 
DELETE|Delete object/s

### Authentication, misc 
Before getting into detailing the meaty part some notes : 
 * Authentication -- I think we should stick to http basic (base64 encoded) over TLS (once known as SSL). Assuming that this is going to be an _API_, used from other software it's easy to add the auth headers always. We can also do cookie auth, though I'm note rally sure of it's usability in our case.
 * Versioning -- It may be an overkill, but it's good design anyway. So API URLs should be in the format :
 
  `http(s)://[ip|name]:[port]/api/v1/...... `
  
This way we keep the API constant and stable for a certain version of the API and clients "speaking" that level should be able to work ok, even after there is a second, third and so on releases of the API. As I said, in this particular case this seems to me a bit of an overkill.
### Objects and collections
We have the following (coarsely defined) groups of "objects" currently :
  * Programs
  * Stations
  * Options
  * Logs
  * System

I've heard people also call these 'collections' in the API world. So the general URL format becomes :

  `http(s)://[ip|name]:[port]/api/v1/[collection]/[object_id]/`

Regarding `object_id`s - we have these even now, though they are more of an implicit type as a result from (I think) array indexing in both OSPy and OS side. They should be explicit.
### Actions 
Since CRUD specifies how one acts *on* objects' definitions we need a way to implement _actions *with*_ these objects. Meaning that stuff like "start this program now", "manual station control" and such, need a way to be cleanly implemented in the API. I propose the `/?do=[action]` notation. See below for more info

## Programs
TODO
### /programs/program_id
### JSON Format
```json
{
    "id": integer, Read-Only
    "enabled": bool,
    "name": string,
    "type": string, one of ["days of week", "interval"]
    "start" : string, HH:MM:SS format
    "duration" : string, HH:MM:SS format
    "scheduling: : string, one of ["single", "recurring"]
    "repeat": string, HH:MM:SS format, recurring scheduling only
    "end" : string, HH:MM:SS format, recurring scheduling only
    "day_of_week": list of integers, days of the week the program needs to run on, week cycle programs only
    "recur": string, "days:after", recur [days] days apart, staring on the [after]th day. [days]<30. interval programs only
    "stations": list of integers, station_ids that will be triggered by the program 
}
```
#### GET
Returns a single station_info entry. Example :
`GET` `/programs/1`
Returns (a weekly cycle, every week day, single pass program)
```json
{
    "id": 1,
    "enabled": true,
    "name": "Weekly demo program",
    "type": "days of week",
    "start" : "06:45:00",
    "duration" : "00:20:00",
    "scheduling: : "single",
    "day_of_week": [1, 2, 3, 4, 5, 6, 7],
    "stations": [1, 3, 6, 7]
}
```

`GET` `/programs/2`
Returns (Interval cycle, repeat every 3 days,recurring every hour and 40 minutes until 20:30)
```json
{
    "id": 2,
    "enabled": true,
    "name": "Interval demo program",
    "type": "interval",
    "start" : "06:45:00",
    "duration" : "00:20:00",
    "scheduling: : "recurring",
    "repeat" : "01:40:00",
    "end" : "20:30:00",
    "recur": "3:2",
    "stations": [2, 4, 5, 11]
}
```
#### POST
TODO
#### PUT
TODO
#### DELETE
TODO
#### Actions
TODO
### /programs/
TODO
#### GET
TODO
#### POST
TODO
#### PUT
TODO
#### DELETE
TODO
#### Actions
TODO

## Stations
### JSON Format
Single station is represented like : 
```json
{
    "id": integer, Read-Only
    "name": string,
    "ignore_rain": bool,
    "enabled": bool,
    "is_master": bool,
    "is_master_two": bool,
    "state": string, Read-Only
    "reason": string Read-Only
}
```
### /stations/station_id/
#### GET
Returns a single station_info entry. Example :
`GET` `/station/1`
Returns
```json
{
    "id": 1,
    "name": "Station One",
    "ignore_rain": "false",
    "enabled": "true",
    "is_master": "true",
    "is_master_two": "false",
    "state": "Running",
    "reason": "Manual start"
}
```
#### POST
This is a bit tricky since stations are "created" only multiples of 8 currently, due to the default shift register output "sub-system" and needs more thought, but in general a `POST` takes a `station_info` object as a parameter and adds it to the `stations` collection
#### PUT
This is the "edit station" method. Takes a "station_info" object and updates station with `id` `station_id`. Example :
`PUT` `/station/1`
```json
{
    "id": 1,
    "name": "Station One With a Nice New Name",
    "ignore_rain": "false",
    "enabled": "true",
    "is_master": "true",
    "is_master_two: "false"
}
```
Renames station 1 to "Station One With a Nice New Name".
#### DELETE
See note for `POST`.
Example:
`DELETE` `/station/1`
Returns nothing.
### /stations/
#### GET
Returns a list of station_info entries, e.g. :
```json
{
    "stations":[
        {
            "id": 1,
            "name": "Station One",
            "ignore_rain": "false",
            "enabled": "true",
            "is_master": "true",
            "is_master_two: "false"
        },
        {
            "id": 2,
            "name": "Station Two",
            "ignore_rain": "false",
            "enabled": "true",
            "is_master": "false",
            "is_master_two: "false"
        },
        ...
    ]
}
```
#### POST
See note for /stations/id.
#### PUT
Not implemented
#### DELETE
Not implemented, or maybe "reset to default" for all stations ? 
#### Actions
Manually start station with id 1. Duration is specified :
`POST` `/stations/1/?do=start`
```json
{
    "duration" : string, HH:MM:SS format 
}
```
Example:
Manually stop station with id 1
`POST` `/stations/1/?do=stop`

## Options
OSPy options
### JSON Format
```json
{
    "system_name": string,
    "location": string,
    "timezone": string,
    "extension_boards": integer,
    "http_port": integer,
    "logs_enabled": bool,
    ...    
}
```
### /options
#### GET
Returns the current system options :
`GET` `/options`
```json
{
    "system_name": "OSPy System",
    "location": "Paris/France",
    "timezone": "Europe/Paris",
    "extension_boards": 1,
    "http_port": 80,
    ...    
}
```
#### POST
Not implemented
#### PUT
`PUT` `/options`
```json
{
    "system_name": "OSPy System",
    "location": "Sahara Desert/Egypt",
    "timezone": "Egypt/Cairo",
    "extension_boards": 4,
    "http_port": 8080,
    ...    
}
```
Modify options
#### DELETE
Not implemented
#### Actions
None

## Logs
OSPy logs
### JSON Format
Log entry
```json
{
    "date": ISO8601 formatted timestamp, Read-Only 
    "message": string, Read-Only
    ...    
}
```
### /logs
#### GET
Returns the current system options. Example :
```json
{
    "logs": [
        {
            "date": "2014-09-20T01:35",
            "message": "Station 3 started"
        },
        {
            "date": "2014-09-20T02:10",
            "message": "Station 3 stopped"
        },
        {
            "date": "2014-09-20T01:40",
            "message": "Very intense log message"
        },
        ...
    ]
}
```
#### POST
Not implemented
#### PUT
Not implemented
#### DELETE
`DELETE` `/logs'
Clears logs
#### Actions
None

## System
OSPy System Data
### JSON Format
System data
```json
{
    "version": string, Read-Only
    "CPU_temp": string, Read-Only
    ...    
}
```
### /system
These are system level data and options, that do not belong to `/options`. Also system level actions are implemented on this resource.
#### GET
Returns the current system options. Example
```json
{
    "version": "2.1.999 (2014-09-10)",
    "cpu_temp": "1000 deg C",
    ...    
}
```
#### POST
Not implemented
#### PUT
Not implemented
#### DELETE
Not implemented
#### Actions
Restart System :
`POST` `/system/?do=restart`

Pull latest from git and restart :
`POST` `/system/?do=git_upgrade`

## Plug-Ins
Access point to everything plug-in related.

TODO: ? plugin repository, format, deployment structure...
### /plugins/plugin_id
plugin specific API calls go under 

`/plugins/plugin_id/<whatever the plugin adds>`

### JSON Format
```json
{
    "id": integer, Read-Only. A name maybe a better id in this particular case
    "enabled": bool,
    "name": string,
    "description": string,
    "status": string, plugin status as reported by the plugin's get_status() method
    ....
}
```
#### GET
Returns a single plugin data. Example :
`GET` `/plugins/1`
Returns 
```json
{
    "id": 1
    "enabled": true,
    "name": "A mega cool plugin for OSPy",
    "description": "World's most famous OSPy plugin"
    "status": "Working, of course"
    ....
}
```
#### POST
TODO
#### PUT
TODO
#### DELETE
TODO
#### Actions
TODO
### /plugins/
TODO
#### GET
List of plugin_info as defined in GET /plugin/plugin_id
#### POST
TODO
#### PUT
TODO
#### DELETE
TODO
#### Actions
TODO
