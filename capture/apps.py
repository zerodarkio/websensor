from django.apps import AppConfig
from django.db.models.signals import post_migrate

import requests
import os
import os.path
import time
from uuid import uuid4
import configparser
import json

from django.conf import settings

def register_sensor(sender, **kwargs):
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    run_once = os.environ.get('CMDLINERUNNER_RUN_ONCE') 
    if run_once is not None:
        return
    os.environ['CMDLINERUNNER_RUN_ONCE'] = 'True'
    from .models import tbl_sensor
    # Check if config file present
    if os.path.isfile(r'/websensor/mount/sensor.conf'):
        config = configparser.ConfigParser()
        config.read_file(open(r'/websensor/mount/sensor.conf'))
        sen_id = config.get('config', 'sensor_id')
        if sen_id != "":
            sen_key = config.get('config', 'sensor_key')
            sen_name = config.get('config', 'sensor_name')
            sen_ip = config.get('config', 'sensor_ip')
            sen_port = config.get('config', 'sensor_port')
            sen_proto = config.get('config', 'sensor_proto')

            tbl_sensor.objects.update_or_create(sensor_id=sen_id, sensor_name=sen_name,
                                          sensor_type=sen_proto, sensor_web_port=sen_port,
                                          sensor_key=sen_key, sensor_ip=sen_ip)

            getconfig()
            exit()

    

    if tbl_sensor.objects.all().exists():
        return
    else:
    
        url = settings.CALLBACKAPI + "/api/register/"

        if os.environ.get("SENSOR_NAME"):
            sen_name = os.environ.get("SENSOR_NAME")
        else:
            sen_name = "intial name"
        
        if os.environ.get("SENSOR_PORT"):
            sen_port = os.environ.get("SENSOR_PORT")
        else:
            sen_port = "80"
        
        if os.environ.get("SENSOR_PROTO"):
            sen_proto = os.environ.get("SENSOR_PROTO")
        else:
            sen_proto = "http"
       
        a = 10
       
        if os.environ.get("SENSOR_IP"):
            sen_ip = os.environ.get("SENSOR_IP")
        else:
            time.sleep(3)
           
            while a != 0:
                ipres = requests.get(settings.CALLBACKAPI + "/api/externalip")
                
                if ipres.status_code == 200:
                    sen_ip = ipres.content.decode('utf8')
                    a = 0
                else:
                    time.sleep(5)
        if not sen_ip:
            
            exit()


        sen_id = str(uuid4())
        data = {}
        data['sensor_id'] = sen_id
        data['name'] = sen_name
        data['ip'] = sen_ip
        data['port'] = sen_port
        data['type'] = sen_proto
        data['version'] = settings.SENSOR_VERSION

        res = requests.post(url, data = data, timeout=5, verify=True)
        if res.status_code == 200:

            sen_key = str(res.text)
            tbl_sensor.objects.create(sensor_id=sen_id, sensor_name=sen_name,
                                      sensor_type=sen_proto, sensor_web_port=sen_port,
                                      sensor_key=sen_key, sensor_ip=sen_ip)
            
            print("PLEASE USE THESE TO ADOPT YOUR SENSOR AT " + settings.CALLBACKAPI + "/sensor/adopt/")
            print("[i] SENSOR ID: " + str(sen_id))
            print("[i] EXTERNAL IP: " + sen_ip)
            
            f = open("/websensor/mount/sensor.conf", "a")
            f.write("[config]")
            f.close()
            config = configparser.ConfigParser()
            config.read_file(open(r'/websensor/mount/sensor.conf'))
            config.set('config', 'sensor_id', sen_id)
            config.set('config', 'sensor_name', sen_name)
            config.set('config', 'sensor_ip', sen_ip)
            config.set('config', 'sensor_port', sen_port)
            config.set('config', 'sensor_proto', sen_proto)
            config.set('config', 'sensor_key', sen_key)
            with open('/websensor/mount/sensor.conf', 'w') as configfile:
                config.write(configfile)
            getconfig()
        else:
            print(str(res.status_code))
            print("[!] Error in setting up sensor")
            exit()


def getconfig():
    from .models import tbl_sensor, tbl_url, tbl_ignore
    defaults = tbl_sensor.objects.get()
    print("[i] Checking for Config Changes")
    url = settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id)
    headers_dict ={'x-zd-api-key': str(defaults.sensor_key)}
    #try:
    x = requests.get(url, headers=headers_dict, timeout=5, verify=True)
    res = x.json()
    data = json.loads(res)

    try:
        defaults.default_html = data['html']
        defaults.default_response_code = data['res_code']
        defaults.default_response_type = data['res_type']
        defaults.default_redirect_link = data['redirect']
    except:
        print("defaults not found")
    defaults.sensor_key = data['key']

    # Pull urls 
    if data['urls']:
        urls = json.loads(data['urls'])
        for i in urls:
            tbl_url.objects.update_or_create(uuid=i['pk'],url_name=i['fields']['url_name'],url=i['fields']['url'],
                                             return_response=i['fields']['return_response'],
                                             response_cookie=i['fields']['response_cookie'],
                                             response_header=i['fields']['response_header'],
                                             response_html=i['fields']['response_html'],
                                             response_code=i['fields']['response_code'],
                                             redirect_url=i['fields']['redirect_url'],
                                             response_type=i['fields']['response_type'])

            headers_dict ={'x-zd-api-key': str(defaults.sensor_key)}
            u_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/url/" + str(i['pk']) + "/ack"
            u_res = requests.get(u_url, headers=headers_dict, timeout=5, verify=True)
            if u_res.status_code == 200:
                defaults.sensor_key = str(u_res.text)
    
    if data['ignores']:
        ignores = json.loads(data['ignores'])
        
        for i in ignores:
            tbl_ignore.objects.update_or_create(ipk=i['pk'],ip=i['fields']['ip'],url=i['fields']['url'])
            headers_dict = {'x-zd-api-key': str(defaults.sensor_key)}
            ig_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/ignore/" + str(i['pk']) + "/ack"
            ig_res = requests.get(ig_url, headers=headers_dict, timeout=5, verify=True)
            if ig_res.status_code == 200:
                defaults.sensor_key = str(ig_res.text)

        defaults.save()

class CaptureConfig(AppConfig):
    name = 'capture'
    
    def ready(self):
        post_migrate.connect(register_sensor, sender=self)




