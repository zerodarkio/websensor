import re
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.template import loader, Template, Context
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.core import serializers

from csp.decorators import csp_exempt

from .models import *

# background tasks
from background_task import background
from background_task.models import Task

from datetime import timedelta
from uuid import UUID,uuid4
import os
import json
import time
import base64 
import sys, traceback
import requests
import configparser

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def callbackcheck(request):
    print(settings.CALLBACKAPI + "/api/health")
    response = requests.get(settings.CALLBACKAPI + "/api/health") 
    return HttpResponse(response, content_type="text/plain", status=200)


def update_conf(sen_key):
    if os.path.isfile("/websensor/mount/sensor.conf"):
        config = configparser.ConfigParser()
        config.read_file(open(r'/websensor/mount/sensor.conf'))
        config.set('config', 'sensor_key', sen_key)
        with open('/websensor/mount/sensor.conf', 'w') as configfile:
            config.write(configfile)
        return
    else:
        print("[i] Sensor.conf not found, unable to write key.")

@background(schedule=60*5)
def getconfig():
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
        defaults.save()
    except:
        print("defaults not found")
    defaults.sensor_key = data['key']
    defaults.save()

    # Pull urls 
    if data['urls']:
        urls = json.loads(data['urls'])
        print(str(urls))

        existing_urls = tbl_url.objects.values_list('uuid', flat=True)
        uuid_list = []
        for a in existing_urls:
            uuid_list.append(str(a))

        for i in urls:
            # need this to make a request for each url
            print("[i] id = " + str(i))
            # check if in db if so skip else pull
            if i not in uuid_list:
                print("[i] url not found and being added: " + str(i))
                get_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/url/" + str(i) + "/"
                y = requests.get(get_url, headers=headers_dict, timeout=5, verify=True)
                get_url_res = y.json()
                get_url_data = json.loads(get_url_res)
                for entry in get_url_data:
                    tbl_url.objects.update_or_create(uuid=entry['pk'],url_name=entry['fields']['url_name'],url=entry['fields']['url'],
                                                 return_response=entry['fields']['return_response'],
                                                 response_cookie=entry['fields']['response_cookie'],
                                                 response_header=entry['fields']['response_header'],
                                                 response_html=entry['fields']['response_html'],
                                                 response_code=entry['fields']['response_code'],
                                                 redirect_url=entry['fields']['redirect_url'],
                                                 response_type=entry['fields']['response_type'])

                u_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/url/" + str(i) + "/ack"
                u_res = requests.get(u_url, headers=headers_dict, timeout=5, verify=True)
            else:
                print("url already present")
        existing_urls2 = tbl_url.objects.values_list('uuid', flat=True)        
        for ex_url in existing_urls2:
            if str(ex_url) not in urls:
                print("[i] url not found and being deleted: " + str(ex_url))
                # Delete the tbl_url_profile object for the url
                tbl_url.objects.filter(uuid=ex_url).delete()

    if data['ignores']:
        existing_ignores = tbl_ignore.objects.values_list('ipk', flat=True)
        ignore_uuid_list = []
        for a in existing_ignores:
            ignore_uuid_list.append(str(a))

        ignores = json.loads(data['ignores'])
        ignore_list = []
        for i in ignores:
            
            ignore_list.append(str(i['ignore_id']))
            if str(i['ignore_id']) not in ignore_uuid_list:

                tbl_ignore.objects.update_or_create(ipk=i['ignore_id'],ip=i['ip'],url=str(i['url']))
                headers_dict = {'x-zd-api-key': str(defaults.sensor_key)}
                ig_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/ignore/" + str(i['ignore_id']) + "/ack"
                ig_res = requests.get(ig_url, headers=headers_dict, timeout=5, verify=True)
            else:
                print("[i] Ignore already present")

        existing_ignores = tbl_ignore.objects.values_list('ipk', flat=True)

        for a in existing_ignores:
            print(str(a))
            print(ignore_list)
            if str(a) not in ignore_list:
                print("[i] Ignore not found and being deleted: " + str(a))
                tbl_ignore.objects.filter(uuid=a).delete()


def getconfig2():
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
        defaults.save()
    except:
        print("defaults not found")
    defaults.sensor_key = data['key']
    defaults.save()

    # Pull urls 
    if data['urls']:
        urls = json.loads(data['urls'])
        existing_urls = tbl_url.objects.values_list('uuid', flat=True)
        uuid_list = []
        for a in existing_urls:
            uuid_list.append(str(a))
        print(type(existing_urls))
        for i in urls:
            # need this to make a request for each url
            # check if in db if so skip else pull
            if i not in uuid_list:
                print("[i] url not found and being added: " + str(i))
                get_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/url/" + str(i) + "/"
                
                y = requests.get(get_url, headers=headers_dict, timeout=5, verify=True)
                get_url_res = y.json()
                
                get_url_data = json.loads(get_url_res)

                for entry in get_url_data:
                    tbl_url.objects.update_or_create(uuid=entry['pk'],url_name=entry['fields']['url_name'],url=entry['fields']['url'],
                                                 return_response=entry['fields']['return_response'],
                                                 response_cookie=entry['fields']['response_cookie'],
                                                 response_header=entry['fields']['response_header'],
                                                 response_html=entry['fields']['response_html'],
                                                 response_code=entry['fields']['response_code'],
                                                 redirect_url=entry['fields']['redirect_url'],
                                                 response_type=entry['fields']['response_type'])

                u_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/url/" + str(i) + "/ack"
                u_res = requests.get(u_url, headers=headers_dict, timeout=5, verify=True)
            else:
                print("[i] url already present")
        existing_urls2 = tbl_url.objects.values_list('uuid', flat=True)        
        for ex_url in existing_urls2:
            if str(ex_url) not in urls:
                print("[i] url not found and being deleted: " + str(ex_url))
                # Delete the tbl_url_profile object for the url
                tbl_url.objects.filter(uuid=ex_url).delete()

    if data['ignores']:
        existing_ignores = tbl_ignore.objects.values_list('ipk', flat=True)
        uuid_list = []
        for a in existing_ignores:
            uuid_list.append(str(a))

        ignores = json.loads(data['ignores'])
        
        ignore_list = []
        for i in ignores:
            
            ignore_list.append(str(i['ignore_id']))
            if str(i['ignore_id']) not in existing_ignores:
                print(str(i['url']))

                tbl_ignore.objects.update_or_create(ipk=i['ignore_id'],ip=i['ip'],url=str(i['url']))
                headers_dict = {'x-zd-api-key': str(defaults.sensor_key)}
                ig_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/ignore/" + str(i['ignore_id']) + "/ack"
                ig_res = requests.get(ig_url, headers=headers_dict, timeout=5, verify=True)
            else:
                print("[i] Ignore already present")
        existing_ignores = tbl_ignore.objects.values_list('ipk', flat=True)
        for a in existing_ignores:
            if str(a) not in ignore_list:
                print("[i] Ignore not found and being deleted: " + str(a))
                tbl_url.objects.filter(uuid=a).delete()



        # Once set and send server the IDs as confirmation
    #except Exception as e:
    #    print("[!] Error on getconfig: " + str(e))
    #return

# hit via /sendLogs
@background(schedule=60*2)
def sendLogs():
    print("Sending Logs")
    defaults = tbl_sensor.objects.get()
    url = settings.CALLBACKAPI + "/api/logs/" + str(defaults.sensor_id)
    # get current logs
    logs = tbl_log.objects.all()
    # store them as json
    logs_json = serializers.serialize('json', logs)
    # send all logs
    x = requests.post(url, data = logs_json, timeout=5, verify=True)
    if x.status_code == 200:
        #delete the logs
        logs.delete()

    return

@csrf_exempt
def index(request, template_name="capture/index.html"):
    try:
       defaults = tbl_sensor.objects.get()
    except Exception as e:
        print("[!] No defaults exist, checking intial data now")
        intial = tbl_sensor(sensor_name="Initial Name")
        intial.save() 
    exception = ""
    response = handler404(request, exception)
    return response

def logger(url_Requested,ip,user_agent,body,requestMethod,cookies,defaults,honey_url_qs,Request_Headers,post_json,get_json,base_url):
    try:
        log = tbl_log(timestamp=timezone.now(),link_requested=url_Requested,
                  src_ip=ip,user_agent=user_agent,request_url=base_url,
                  request_body=body, request_method=requestMethod, request_cookies=cookies,
                  src_sensor=defaults, honeyurl=honey_url_qs, request_headers=Request_Headers,
                  request_post_parameters=post_json,request_get_parameters=get_json)
        log.save()
        print("[i] Saved request to logs")
        if Task.objects.filter(verbose_name="sendLogs").exists():
            print("[i] Already have sendLogs waiting")
        else:
            sendLogs(repeat=Task.NEVER, verbose_name="sendLogs")

        if Task.objects.filter(verbose_name="getconfig").exists():
            print("[i] Already have getconfig waiting")
        else:
            getconfig(repeat=Task.NEVER,verbose_name="getconfig") 
        return
    except Exception as e:
        print("[!] Error logger failed: " + str(e))
        return

def get_client_ip(request):
	# Modified Nginx to change the IP to HTTP_X_REAL_IP
    x_forwarded_for = request.META.get('HTTP_X_REAL_IP')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
@csp_exempt
def handler404(request, exception,template_name="capture/response.html"):
    
    # Get Defaults
    defaults = tbl_sensor.objects.get()
    redirect = str(defaults.default_redirect_link)

    # Get Date Time
    today = timezone.now()

    #### Pull Request Data ####

    # We have to pull the request info
    # Get Real IP
    ip = str(get_client_ip(request))
    
    # Grab Method
    requestMethod = str(request.method)
    
    # Grab URL with and without Parameters
    url_Requested = str(request.get_full_path_info())
    base_url = request.path_info # without get parameters

    # Check if its an Assets URL - Put here to reduce load.
    if url_Requested.split("/")[1] == "assetss":
        #print("assets hit")
        return HttpResponse("File Not Found", content_type="text/plain", status=404)
    
    if url_Requested == "/" + str(defaults.sensor_id) + "/get":
        print("Getting config...")
        getconfig2()
        try:
            template_code = base64.b64decode(str(defaults.default_html).encode())
        except:
            template_code = "Error"
        response = HttpResponse(template_code)
        response["Content-Type"] = defaults.default_response_type
        response.status_code = defaults.default_response_code
        return response

    # Grab Request Body
    body = str(request.body)
    
    # Cookies
    cookies = str(request.COOKIES)
   
    # Host
    try:
        host = request.META['HTTP_HOST']
    except Exception as e:
        print("[!] Error getting Host Header")
        host = ""
    
    # User Agent
    try:
        user_agent = request.META['HTTP_USER_AGENT']
    except Exception as e:
        print("[!] Error getting User Agent Header")
        user_agent = ""
    
    # Grab Raw Headers 
    try:
        Request_Headers = str(request.headers)
    except Exception as e:
        print("[!] Failed to pull headers:" + str(e))
        Request_Headers = ""


    # TODO - Check for GET Parameters
    get_json = ""
    if request.GET:
        print("trying to pull GET parameters")
        get_params = request.GET
        get_json = json.dumps(get_params)
        print(get_json)
        

    # TODO - Check for POST Parameters
    post_json = ""
    if request.POST:
        print("trying to pull POST parameters")
        post_params = request.POST
        post_json = json.dumps(post_params)
        print(post_json)


    ###### Ignore Checks #######    

    # Check URL if ignore
    if tbl_ignore.objects.filter(url__iexact=url_Requested).count() >= 1:              
        try:
            template_code = base64.b64decode(str(defaults.default_html).encode())
        except:
            template_code = "Error"
        response = HttpResponse(template_code)
        response["Content-Type"] = defaults.default_response_type
        response.status_code = defaults.default_response_code
        return response

    # Check Source IP matches ignore
    if tbl_ignore.objects.filter(ip__iexact=ip).count() >= 1:               
        try:
            template_code = base64.b64decode(str(defaults.default_html).encode())
        except:
            template_code = "Error"
        response = HttpResponse(template_code)
        response["Content-Type"] = defaults.default_response_type
        response.status_code = defaults.default_response_code
        return response

    # Check User agent matches ignore
    
    # Grab all Urls    
    urls = tbl_url.objects.all()
    

    #### Honey URL Checks ####

    if urls.filter(url__iexact=url_Requested).count() == 1:
        url_qs = urls.get(url__iexact=url_Requested)
        print("[i] URL hit is called:" + str(url_qs.url_name))
    elif urls.filter(url__iexact=base_url).count() == 1:
        url_qs = urls.get(url__iexact=base_url)
        print("[i] URL hit is called:" + str(url_qs.url_name))
    else:
        print("[i] Unknown URL hit:" + str(url_Requested))
        url_qs = type(None)()
        logger(url_Requested,ip,user_agent,body,requestMethod,cookies,defaults,url_qs,Request_Headers,post_json,get_json,base_url)
        try:
            template_code = base64.b64decode(str(defaults.default_html).encode())
        except:
            template_code = "Error"
        response = HttpResponse(template_code)
        response["Content-Type"] = defaults.default_response_type
        response.status_code = defaults.default_response_code
        return response

    # Check if there is a Response Code to be set
    if url_qs.response_code:
        response_code = url_qs.response_code
    else:
        response_code = 200
    try: 
        # Check if there is Response cookies to be set        
        if url_qs.response_cookie:
            print("[i] Setting cookie values")
            cookie_json = json.loads(url_qs.response_cookie)
    except:
        print("[!] Invalid cookie json provided!")
    
    # Check if there is Response Headers to be set
    try:
        if url_qs.response_header:
        print("[i] Setting header values")
        header_json = json.loads(url_qs.response_header)
    except:
        print("[!] Invalid header json provided!")

    
    # TODO - Check for Web Call Back Setting

    # TODO - Make sure to add a Host Header to the DB

    # Log the request         
    log = tbl_log(timestamp=timezone.now(),link_requested=url_Requested,
                  src_ip=ip,user_agent=user_agent,
                  request_body=body, request_get_parameters=get_json,
                  request_post_parameters=post_json,
                  request_method=requestMethod, request_cookies=cookies,
                  src_sensor=defaults, honeyurl=url_qs)
    log.save()
     

    # Check if there is Redirct Response
    if url_qs.redirect_url:
        print(url_qs.redirect_url + "/a")
        return HttpResponseRedirect(str(url_qs.redirect_url))
        #return redirect(str(url_qs.redirect_url + "/") )

    # Return Response
    response_data = base64.b64decode(str(url_qs.response_html).encode())
    response = HttpResponse(response_data)
    
    # Try and Add the Headers to the Response
    try:
        if header_json:
            print("get here in headers!")
            for h_entry in header_json['headers']:
                print("Header_Name : " + h_entry['header_Name'])
                print("Header_Value : " + h_entry['header_value'])
                response[h_entry['header_Name']] = h_entry['header_value']
    except Exception as e:
       print("[!] No headers captured: " + str(e))

    # Try and Add Cookies to the Response
    try:
        if not cookie_json:
            for c_entry in cookie_json['cookies']:
                response[c_entry['cookie_Name']] = c_entry['cookie_value']
    except:
        print("[!] No Cookies captured")
    
    # Add Response Type to the Response 
    response["Content-Type"] = url_qs.response_type# + str("; charset=utf-8")
    response.status_code = response_code #response_code
    return response


# Add in 500 Error Code Here 
@csrf_exempt
def handler500(request, *args, **argv):
    #return HttpResponseServerError()
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("*** print_tb:")
    traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
    print("*** print_exception:")
    traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
    print("*** print_exc:")
    traceback.print_exc()
    print("*** format_exc, first and last line:")
    formatted_lines = traceback.format_exc().splitlines()
    print(formatted_lines[0])
    print(formatted_lines[-1])
    print("*** format_exception:")
    print(repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)))
    print("*** extract_tb:")
    print(repr(traceback.extract_tb(exc_traceback)))
    print("*** format_tb:")
    print(repr(traceback.format_tb(exc_traceback)))
    print("*** tb_lineno:", exc_traceback.tb_lineno)
    template_name="capture/response.html"
    response = render(request, template_name)
    response.status_code = 500
    return response
