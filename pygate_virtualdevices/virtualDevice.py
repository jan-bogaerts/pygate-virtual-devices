__author__ = 'Jan Bogaerts'
__copyright__ = "Copyright 2016, AllThingsTalk"
__credits__ = []
__maintainer__ = "Jan Bogaerts"
__email__ = "jb@allthingstalk.com"
__status__ = "Prototype"  # "Development", or "Production"

import requests
import json
import logging
import os
import yaml
logger = logging.getLogger('virtual devices')

_servicesLocation = "virtualservices"

def getDataSourceName(value):
    """
    extracts the data source that was defined in value. Value must be of the form datasource[xxx]
    :param value: a string, Value must be of the form datasource[xxx]  , also allowed: datasource[xxx][n][n]
    :return: xxx (name of datasource) + the index selectors that follow the datasource.
    """
    parts = value.split('[')
    if len(parts) == 2:
        return parts[1][:-1], None                    #remove the last ']'
    elif len(parts) == 3:
        return parts[1][:-1], [x[:-1]  for x in parts[2:]]  # remove the last ']'
    else:
        raise Exception("invalid data source in path")

def selectField(value, field):
    """
    returns a sub section of a json dict, based on the specified field.
    :param value:
    :param field:
    :return:
    """
    parts = field.split('[')
    if len(parts) == 1:
        name, indexes = parts[0], None
    elif len(parts) > 1:
        name, indexes = parts[0], parts[1:]
    else:
        raise Exception("invalid section in path")
    curPos = value[name]
    if indexes:
        for index in indexes:
            if not curPos:
                raise Exception("end of data reached, can't finish query after field: " + field)
            indexPos = int(index[:-1])  # remove the [ at end and turn into int so we can use as index
            curPos = curPos[indexPos]
    return curPos

def getValue(definition, queryResults):
    """
    return a json object that is created based on the definition, using the values found in the query results.
    :param definition: a template json object that cntains 'query' objects instead of basic values.
    :param queryResults: the query results to use.
    :return:
    """
    if 'query' in definition:  # when byte is a field, then we are producing a basic value, otherwise we are creating an object or list.
        return queryResults[definition['query']]
    elif 'object' in definition:
        value = {}
        for key, data in definition['object'].iteritems():
            value[key] = getValue(data, queryResults)
        return value
    elif 'list' in definition:
        value = []
        for data in definition['list']:
            value.append(getValue(data, queryResults))
        return value


def loadDefinition(name):
    """loads the service definition from file and returns it as a json object."""
    fileName = os.path.join(_servicesLocation, name + '.json')
    if not os.path.isfile(fileName):
        logger.error('file not found ' + fileName)
        return None
    else:
        with open(fileName) as json_file:
            logging.info("loading " + fileName)
            #json_data = yaml.safe_load(json_file)
            json_data = json.load(json_file)
            return json_data


class VirtualDevice(object):
    """
    represents a website that can be queried for data and represented as a device.
    """

    def __init__(self, name, values, id):
        """
        load a virtual device from the definition
        :param name:  name of file that contains json dict with the entire definition of the virtual device
        :param values: the values for the variable sections in the definition.
        :param id: the id (local, on the gateway ) of this virtual device.
        """
        self._dataSources = {}
        definition = loadDefinition(name)
        self.id = id
        if not definition:
            return
        else:
            self.loadFromDefinition(definition, values)

    def loadFromDefinition(self, definition, values):
        """
        preparet the object from the json service definition.
        :param definition:  name of file that contains json dict with the entire definition of the virtual device
        :param values: the values for the variable sections in the definition.
        :return:
        """
        try:
            for ds in definition['data sources']:
                for key, value in values.iteritems():  # replace variable sections in the uri
                    ds['uri'] = str(ds['uri']).replace("{{" + key + "}}", value)
                if 'body' in ds:  # if there is a body section, also replace params
                    for key, value in values:
                        ds['body'] = json.dumps(ds['body']).replace("{{" + key + "}}", value)
                if 'headers' in ds:  # if there is a header section, also replace params
                    newHeaders = {}  # make a cpopy of the dict cause the keys can change as well.
                    for header_key, header_value in ds['headers'].iteritems():  # headers has to be a dict.
                        for key, value in values:
                            header_key = header_key.replace("{{" + key + "}}", value)
                            header_value = header_value.replace("{{" + key + "}}", value)
                        newHeaders[header_key] = header_value
                    ds['headers'] = newHeaders
                self._dataSources[str(ds['name'])] = ds

            self._queries = definition['queries']
            self._assets = definition['values']
            self.refreshRate = definition['refresh rate']  # need this to schedule the jobs.
        except:
            logger.exception("failed to load service")

    def getDataSourceResult(self, name):
        """
        perform a http rest call to the specified data source and return the content.
        :return: a string representing the body of the http call, if succesfull.
        """
        ds = self._dataSources[name]
        if ds:
            if 'method' in ds:
                method = ds['method']
            else:
                method = 'get'
            if 'body' in ds:
                body = json.loads(ds['body'])                   # the body is stored as a string so that we could replace the variable parts
            else:
                body = None
            if 'headers' in ds:
                headers = ds['headers']
            else:
                headers = None
            r = requests.request(method.upper(), ds['uri'], headers=headers, json=body)
            if 'response' in ds:
                if r.status_code != ds['response']:
                    logger.error("invalid response: {}, {} from datasource: {} in device: {}".format(r.status_code, r.reason, name, self.id))
                    return None
            return json.loads(r.content)
        else:
            logger.error("unknown datasource: {} in device: {}".format(name, self.id))

    def runQuery(self, queryStr, dataSourceResults):
        """
        Run the query and return the result.
        :param queryStr: a string that contains the query (json path selector)
        :param dataSourceResults: a dict that contains the api result (json dict) of each data source that has already been requested this run.
        :return: the json value that was found in the data source result, at the location defined by the query.
        """
        queryParts = queryStr.split('.')
        if queryParts[0].startswith('datasource'):
            ds, indexes = getDataSourceName(queryParts[0])
        else:
            raise Exception("query has to start with datasource")
        if not ds in dataSourceResults:
            dataSourceResults[ds] = self.getDataSourceResult(ds)
        dsResult = dataSourceResults[ds]
        if dsResult:
            curPos = dsResult  # we start at the beginning of the json dict
            if indexes:
                for index in indexes:
                    indexPos = int(index[:-1])              # remove the [ at end and turn into int so we can use as index
                    curPos = curPos[indexPos]
            for part in queryParts[1:]:                     # skip first item, we already processed this
                curPos = selectField(curPos, part)
            return curPos



    def run(self, gateway):
        """
        run all the queries and send the values to the assets.
        :return:
        """
        queryRes = {}
        dataSourceResults = {}
        for query in self._queries:
            try:
                queryRes[query['name']] = self.runQuery(query['value'], dataSourceResults)
            except:
                logger.exception("failed to run query : {} in virtual device".format(self.id))

        for asset in self._assets:
            try:
                value = getValue(asset['value'], queryRes)
                if value:
                    gateway.send(value, self.id, asset['asset'])
            except:
                logger.exception("failed to send value for asset: " + asset['asset'])


    def addDevice(self, gateway, label):
        """
        adds this device to the gateway
        :param label: the label for the devce
        :param gateway: the gateway object to add the device to.
        :return: None
        """
        gateway.addDevice(self.id, label, "a virtual device")
        self.updateDevice(gateway)

    def updateDevice(self, gateway):
        """
        adds this device to the gateway
        :param gateway: the gateway object to add the device to.
        :return: None
        """
        for asset in self._assets:
            gateway.addAsset(asset['asset'], self.id, asset['label'], asset['label'], False, asset['type'], 'Undefined')
