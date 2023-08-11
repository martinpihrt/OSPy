API Details
====
Not all functionality is complete.

### HTTP Method Mapping
|Method|Mapping|
|:--|:--|
GET|Get / List object/s
PUT|Update / modify object/s
POST|Create new object/s 
DELETE|Delete object/s

### Authentication, misc 
Before getting into detailing the meaty part some notes: 
 * Authentication -- I think we should stick to http basic (base64 encoded) over TLS (once known as SSL). Assuming that this is going to be an _API_, used from other software it's easy to add the auth headers always. We can also do cookie auth, though I'm note rally sure of it's usability in our case.
 * Versioning -- It may be an overkill, but it's good design anyway. So API URLs should be in the format:
 
  `http(s)://[ip|name]:[port]/api/...... `

In Header for http GET/POST response:
`Header("Authorization", "Basic " "Username:Password")` 
  
This way we keep the API constant and stable for a certain version of the API and clients "speaking" that level should be able to work ok, even after there is a second, third and so on releases of the API. As I said, in this particular case this seems to me a bit of an overkill.
### Objects and collections
We have the following (coarsely defined) groups of "objects" currently:
  * Programs
  * Stations
  * Options
  * Logs
  * System
  * Sensors
  * Sensor
  * User
  * Balance
  * Plugin Footer
  * Plugin
  * Runonce

I've heard people also call these 'collections' in the API world. So the general URL format becomes:

  `http(s)://[ip|name]:[port]/api/[collection]/[object_id]/`

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
Returns a single station_info entry. Example:
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
Single station is represented like: 
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
Returns a single station_info entry. Example:
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
Returns a list of station_info entries, e.g.:
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
Not implemented, or maybe "reset to default" for all stations? 
#### Actions
Manually start station with id 1. Duration is specified:
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
Returns the current system options:
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
Returns the current system options. Example:
```json
[
    {
        "start": 1688096105, 
        "end": 1688097725, 
        "duration": "0:26:59", 
        "manual": false, 
        "station": 5, 
        "station_name": "6. vchod", 
        "program_id": 6, 
        "program_name": "Vchod"
    },
    {
        "start": 1688097730, 
        "end": 1688098030, 
        "duration": "0:04:59", 
        "manual": false, 
        "station": 3, 
        "station_name": "4. krm\u00edtko",
        "program_id": 3,
        "program_name": "Krmitko"
    },
    {
        "start": integer, Read-Only. Start timestamp. 
        "end": integer, Read-Only. Stop timestamp. 
        "duration": string, Read-Only. Format hours:minutes:seconds.
        "manual": bool, Read-Only. If it is false, then it is not a manual program but a scheduler.
        "station": integer, Read-Only. Station ID.
        "station_name": string, Read-Only. Station name in UTF format.
        "program_id": integer, Read-Only. Program ID.
        "program_name": string, Read-Only. Program name in UTF format.
     }
]
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
### /system
These are system level data and options, that do not belong to `/options`. Also system level actions are implemented on this resource.
#### GET
Returns the current system options. Example:
```json
{
    "version": "3.0.52",
    "CPU_temperature": "-",
    "release_date": "2023-07-31",
    "uptime": "1. day 20:54",
    "platform": "pi",
    "rpi_revision": 3,
    "total_adjustment": 1.0
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
Available commands: reboot, restart, poweroff

### /sensors
These are sensor data `/sensors`.
#### GET
Returns the current sensors options. Example:
`GET` `/sensors/1`
 Returns
```json
{
    "id": 1,
    "enabled": true,
    "senstype": 6,
    "senscom": 0,
    "logsamples": true, 
    "logevent": false, 
    "sendemail": false, 
    "samplerate": 3600, 
    "lastreadvalue": "[17.3, -127.0, -127.0, -127.0, 1, 0.0, 0.0, 0, 22]", 
    "sensitivity": 0, 
    "stabilizationtime": 5, 
    "triglowpgm": "['-1']", 
    "trighighpgm": "['-1']", 
    "triglowval": "0", 
    "trighighval": "40", 
    "lastbattery": "12.7", 
    "rssi": "46", 
    "response": 1, 
    "last_response": 1690884885.2562356, 
    "last_response_datetime": "2023-08-01 10:14:45", 
    "fw": "119", 
    "show_in_footer": 1, 
    "cpu_core": 0, 
    "distance_top": 10, 
    "distance_bottom": 95, 
    "water_minimum": 10, 
    "diameter": 100, 
    "check_liters": 0, 
    "use_stop": 0, 
    "use_water_stop": 0, 
    "used_stations": ["-1"], 
    "used_stations_one": ["-1"], 
    "used_stations_two": ["-1"], 
    "enable_reg": 0, 
    "reg_max": 100, 
    "reg_mm": 60, 
    "reg_ss": 0, 
    "reg_min": 90, 
    "reg_output": 0, 
    "delay_duration": 0, 
    "soil_last_read_value": [-127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0, -127.0],
    "soil_calibration_min": [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0], "soil_calibration_max": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "soil_program": ["-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1", "-1"]
}
```
#### POST
Not implemented
#### PUT
Not implemented
#### DELETE
Not implemented
#### Actions
Not implemented

### /sensor
These are sensor data `/sensor`.
Example:
Send data from sensor.
`POST` `/sensor?do={json format}&sec=AES_string`
Example:
`# Example: do={"ip":"192.168.88.210","mac":"aa:bb:cc:dd:ee:ff","rssi":"52","batt":"123","stype":"5","scom":"0","temp":"253","drcon":"1","lkdet":"125","humi":"658","moti":"1"}&sec="Vno7I7aD2E44455"`       

#### GET
Not implemented
#### PUT
Not implemented
#### DELETE
Not implemented
#### Actions
Not implemented

### /user
When login data is sent in the header, information about the category the user belongs to is returned.
#### GET
Returns
```json
{
    "user": string, Read-Only. User name. 
    "category": string, Read-Only. User category ex: admin. 
}
```
Category types: sensor, public, user, admin

#### POST
Not implemented
#### PUT
Not implemented
#### DELETE
Not implemented
#### Actions
Not implemented

### /balances
Balances returns data to create a graph with times and dates of stations running. It is also possible to obtain information such as: station name, time stamp, ETo, amount of rain, run interval, total balance.
#### GET
Returns
```json
[
  {
    "station": string, Read-Only. Station name label.
    "balances": {
      "1689033600": { string, Read-Only. Start timestamp.
        "eto": integer, Read-Only. Loss of water ETo factor in mm, more information about ETo is in OSPys help.
        "rain": float, Read-Only. The value of how many mm of rain fell.
        "intervals": [
          {
            "program": integer, Read-Only. Identification for program ID.
            "program_name": string, Read-Only. Program name label.
            "done": bool, Read-Only. Information about the running entire program.
            "irrigation": float, Read-Only. The value of how many mm were added by the running program.
          }
        ],
        "total": float, Read-Only. Total water balance in mm (adding and subtracting all factors. For example: rain+, program+, ETo-).
        "valid": bool, Read-Only. Information for creating a chart. Its not important here.
      },
      "1689120000": {
        "eto": 1.5,
        "rain": 0.0,
        "intervals": [],
        "total": -10.198076462499978,
        "valid": true
      },
      "1689206400": {
        "eto": 1.5,
        "rain": 0.0,
        "intervals": [
          {
            "program": 2,
            "program_name": "program name label 1",
            "done": true,
            "irrigation": 5.833185536111111
          }
        ],
        "total": -5.864890926388867,
        "valid": true
      },
      
    }
  },
  {
    "station": "station name label 2",
    "balances": {
      "1689033600": {
        "eto": 1.5,
        "rain": 0.0,
        "intervals": [
          {
            "program": 5,
            "program_name": "program name label 2",
            "done": true,
            "irrigation": 3.4007758469444447
          }
        ],
        "total": -70.47103433847222,
        "valid": true
      },
      "1689120000": {
        "eto": 1.5,
        "rain": 0.0,
        "intervals": [],
        "total": -71.97103433847222,
        "valid": true
      },
      "1689206400": {
        "eto": 1.5,
        "rain": 0.0,
        "intervals": [
          {
            "program": 5,
            "program_name": "program name label 2",
            "done": true,
            "irrigation": 3.3968468352777776
          }
        ],
        "total": -70.07418750319445,
        "valid": true
      },
      "1689292800": {
        "eto": 1.5,
        "rain": 0.0,
        "intervals": [
          {
            "program": 5,
            "program_name": "program name label 2",
            "done": true,
            "irrigation": 3.3962396236111108
          }
        ],
        "total": -68.17794787958334,
        "valid": true
      }
    }
  }
]
```

#### POST
Not implemented
#### PUT
Not implemented
#### DELETE
Not implemented
#### Actions
Not implemented

### /pluginfooter
In the "fdata" list, data can be read from running plugins that are enabled to display data on the home page. In the "sendata" list, data can be read from running sensors that are enabled to display data on the home page.
#### GET
Returns
```json
{
    "fdata": [
        [
            0, "System Update", "Up-to-date", "", "system_update/status"
        ],
        [
            integer, Plugin ID.
            string, Label for plugin name.
            string, Plugin Data.
            string, Unit (for example, degrees Celsius. Usually not used because it is already included directly in the data).
            string, Link to the plugin (for use in the button. For example: air_temp_humi/settings is the full path: IP:PORT/plugins/air_temp_humi/settings.
        ]        
    ],
    "sendata": [
        [
            "test", "Not response!", 0
        ],
        [
            string, Label for sensor name.
            string, Sensor Data.
            integer, Sensor ID.
        ]
    ]
}
```
#### POST
Not implemented
#### PUT
Not implemented
#### DELETE
Not implemented
#### Actions
Not implemented


## Runonce
Allows you to start the selected station for a set time (the duration is entered in seconds).
#### GET
Not implemented
#### PUT
Not implemented
#### DELETE
Not implemented
#### POST
Returns 
```
    "OK"
```
#### Actions
Example:
Manually start station with id 2. Duration is 10 seconds:
`POST` `/runonce/1/?time=10`
Manually start station with id 1. Duration is 30 seconds:
`POST` `/runonce/0/?time=30`


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
Returns a single plugin data. Example:
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
