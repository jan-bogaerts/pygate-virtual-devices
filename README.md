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

# add new virtual device definitions 


