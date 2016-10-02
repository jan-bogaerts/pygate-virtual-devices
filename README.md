# Description
This is a plugin for [pygate](https://github.com/allthingstalk/pygate): add virtual devices to the gateway such as online weather stations.

#installation


- Make certain that [pygate](https://github.com/allthingstalk/pygate) and all of it's dependencies have been installed first.
- download the module
- install the module, 2 options are available:
	- run `python setup.py install` from within the plugin directory  
	- or copy the directory pygate_virtualdevices to the root directory of the pygate software (at the same level as pygate.py)  
and run `pip install -r requirements.txt` from within the pygate_virtualdevices directory.
- install the virtual device definitions:
	- copy the directory virtualdevices to the root directory of the pygate software

#activate the plugin
the plugin must be activated in the pygate software before it can be used. This can be done manually or through the pygate interface.

## manually
Edit the configuration file 'pygate.conf' (located in the config dir).
add 'virtualdevices' to the config line 'modules' in the general section of the 'pygate.conf' config file. ex:  
    
	[general]  
    modules = main; virtualdevices; liato
When done, restart the gateway.

##pygate interface
Use the actuator 'plugins' and add 'virtualdevices' to the list. After the command has been sent to the device, the gateway will reboot automatically.

# configure available virtual devices
No virtual devices are loaded by default. You will have to configure the list of virtual devices that should be maintained (and thus the web api's that have to be queried).

- create a file callled 'virtualdevices.json' in 'config'. This contains a json array with device configurations
- for each virtual device, create a json object with the following fields:
	- name: the name of the device, should only contains characters, numbers, dashes or underscores (no spaces). This is used as an identifier and is not displayed to the user.
	- label: this is the display name and can be a free form string.
	- service: the name of the virtual device definition that should be used. The service defines which api should be queried, and how (see further).
	- params: a json object that contains a field for each parameter that has to be supplied to the definition. The exact list of required parameters is defined in the definition itself.

Example:

```json
[
  {
    "name": "weather_station_Temse",
    "label": "weather station Temse",
    "service": "weather service",
    "params": {
      "location": "Temse",
      "key": "xxxx"
    }
  },
  {
    "name": "weather_station_Gent",
    "label": "weather station Gent",
    "service": "weather service",
    "params": {
      "location": "Gent",
      "key": "xxx"
    }
  }
]
```

# virtual device definitions
The actual api's that should be queried, are defined in 'virtual device definitions'. Such a definition is a json object that declares the api endpoint to call, optional parameters for the url, headers and or body and a way to translate the result of the api call into asset values.
The definition should contain the following fields:

- name: the name of the definition. This is used in the file 'virtualdevices.json' as the value for the field 'service'
- author: optional field, string. Defines the creator of the definition.
- refresh rate: determins the period by which the api is refreshed. This is a string in the form 'days:hours:minutes.  
ex: `"0:4:0"` -> the service will be queried every 4 hours.
variables: an array of variables that have to be supplied to the definition. This maps to the field 'params' in the file 'virtualdevices.json'. The array contains a list of json objects, each containing the following fields:
	- name: the name of the variable
	- type: the data type of the variable. Currently supported: boolean, string, number (json types).  
ex:
```
{
			"name" : "location",
			"type" : "string"
		}
```
- data sources: this is a array of json objects. Each object defines an url endpoint that can be queried for this service. The following fields are used:
	- name: the name of the data source. This is used in the 'queries' (see later) to find the resource who's result is used.
	- uri: the uri to query. This is a string that can contain references to variables. Each variable name has to be enclosed by 2 brackets. ex:  `"uri" : "http://api.worldweatheronline.com/free/v1/weather.ashx?q={{location}}&format=json&num_of_days=5&key={{key}}"`
	- method: supported values: get, put, post, delete
	- body: (optional) an optional body that has to be sent with the request. The body can also contain variable references like the uri.  ex:  
```
"body": {"value":"{{value}}"}
```
	- headers: (optional): a dictionary of header name and value. Both name and value can contain references to variable values. ex:  
```
"headers": {"header1":"{{header1val}}", "{{header1name}}": "a value"}
```
	- response: (optional) a number that should be returned as response of the call to the uri. ex: 200


