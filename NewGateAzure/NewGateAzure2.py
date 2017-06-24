import urllib, sys, datetime, time
import urllib2
import gc

def send_iot():
    iot_device_id = 'HTTP_Device'
    iot_endpoint = 'https://winiothub.azure-devices.net/devices/' + iot_device_id + '/messages/events?api-version=2016-02-03'
    sas_header = {'Authorization': 'SharedAccessSignature sr=winiothub.azure-devices.net%2Fdevices%2FHTTP_Device&sig=o7dndsA%2FJOnkzYRUhqAwMrQXVhOTpIJqJqILyGDdQAc%3D&se=1522414643'}
    try:
        body_data = { 'gateway_serial': '123', 'readingvalue':'66.00', 'date': str(datetime.datetime.now())}
        iot_request = urllib2.Request(iot_endpoint, str(body_data), sas_header)
        try:
            resp = urllib2.urlopen(iot_request)
        except urllib2.HTTPError, e:
            raise
            if e.code ==  204:
                print '204'
            else:
                print 'Error = ' + e.code
        contents = resp.read()
        print gc.collect()
        resp.close()
        time.sleep(1)
    except urllib2.HTTPError, e:
        if e.code == 204:
            print '204'
            pass
        else:
            print 'error' 
        time.sleep(1)


while True:
    send_iot()