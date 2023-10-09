import re
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.template import loader, Template, Context
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.core import serializers
from django.db.models import Q

from django.core.exceptions import ObjectDoesNotExist

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
import html
import ast

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

@background(schedule=60*2)
def getconfig():
    getconfig2()
    

def getconfig2():
    defaults = tbl_sensor.objects.get()
    print("[i] Checking for Config Changes")
    url = settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id)
    headers_dict ={'x-zd-api-key': str(defaults.sensor_key)}
    #try:
    x = requests.get(url, headers=headers_dict, timeout=5, verify=True)
    print("================ raw response ============")
    print(x.content)
    res = x.json()
    data = json.loads(res)
    print("================ All json loads ============")
    print(data)
    print("================")
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
        print("================ data[urls] ============")
        print(data['urls'])
        print("================")
        existing_urls = tbl_url.objects.values_list('uuid', 'url_hash', named=True)
        uuid_list = []
        hash_list = []
        missing_list = []
        urls = ast.literal_eval(data['urls'])
        print("================ urls list ============")
        print(urls)
        print(type(urls))
        print("================")
        for url in urls:
            print("================ url value in for loop ============")
            print(url)
            print(type(url))
            print("================")
            url_uuid = url.split("'")[1]
            uuid_list.append(url_uuid)
            url_hash = url.split("'")[3]
            print("================ url_uuid value in for loop ============")
            print(url_uuid)
            print(type(url_uuid))
            print("================")
            print("================ url_hash value in for loop ============")
            print(url_hash)
            print(type(url_hash))
            print("================")
            if url_uuid and url_hash:
                if not any(existing_url.uuid == url_uuid and existing_url.hash == url_hash for existing_url in existing_urls):
                    missing_list.append(url_uuid)

            print("================ missing_list value in for loop ============")
            print(missing_list)
            print(type(missing_list))
            print("================")
            """urls = json.loads(data['urls'])
                                    existing_urls = tbl_url.objects.values_list('uuid', flat=True)
                                    uuid_list = []
                                    for a in existing_urls:
                                        uuid_list.append(str(a))
                                    print(type(existing_urls))"""
            for i in missing_list: #urls:

                get_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/url/" + str(i) + "/"
                
                y = requests.get(get_url, headers=headers_dict, timeout=5, verify=True)
                get_url_res = y.json()
                
                get_url_data = json.loads(get_url_res)

                for entry in get_url_data:
                    try:
                        obj = tbl_url.objects.get(url=entry['fields']['url'])
                        # Update the existing object
                        obj.uuid = entry['pk']
                        obj.url_name = entry['fields']['url_name']
                        obj.return_response = entry['fields']['return_response']
                        obj.response_cookie = entry['fields']['response_cookie']
                        obj.response_header = entry['fields']['response_header']
                        obj.response_html = entry['fields']['response_html']
                        obj.response_code = entry['fields']['response_code']
                        obj.redirect_url = entry['fields']['redirect_url']
                        obj.response_type = entry['fields']['response_type']
                        url_hash=entry['fields']['url_hash']
                        # Save the changes
                        obj.save()
                        print(f"added {obj.url_name} with uuid: {str(obj.uuid)}")
                    except ObjectDoesNotExist:
                        # Create a new object
                        obj = tbl_url.objects.create(
                            uuid=entry['pk'],
                            url_name=entry['fields']['url_name'],
                            url=entry['fields']['url'],
                            return_response=entry['fields']['return_response'],
                            response_cookie=entry['fields']['response_cookie'],
                            response_header=entry['fields']['response_header'],
                            response_html=entry['fields']['response_html'],
                            response_code=entry['fields']['response_code'],
                            redirect_url=entry['fields']['redirect_url'],
                            response_type=entry['fields']['response_type'],
                            url_hash=entry['fields']['url_hash']
                        )

                u_url =  settings.CALLBACKAPI + "/api/config/" + str(defaults.sensor_id) + "/url/" + str(i) + "/ack"
                u_res = requests.get(u_url, headers=headers_dict, timeout=5, verify=True)
                print(str(u_res.status_code))
                #else:
                #    print("[i] url already present")
            existing_urls2 = tbl_url.objects.values_list('uuid', flat=True)
            uuid_list #= [re.search(r"UUID\('([^']+)", url).group(1) for url in urls]       
            for ex_url in existing_urls2:
                if str(ex_url) not in uuid_list:
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

    return



        # Once set and send server the IDs as confirmation
    #except Exception as e:
    #    print("[!] Error on getconfig: " + str(e))
    #return

# hit via /sendLogs
@background(schedule=60*1)
def sendLogs():
    print("Sending Logs")
    try:
        defaults = tbl_sensor.objects.get()
        url = settings.CALLBACKAPI + "/api/logs/" + str(defaults.sensor_id)
    except ObjectDoesNotExist:
        print("No default sensor object found.")
        return
    all_logs = list(tbl_log.objects.all().order_by('date', 'timestamp'))
    while all_logs:
        batch_logs = all_logs[:3]
        print(batch_logs)
        all_logs = all_logs[3:]
        try:
            logs_json = serializers.serialize('json', batch_logs)
        except Exception as e:
            print(f"Error on serializing logs: {str(e)}")
        
        try:
            x = requests.post(url, data=logs_json, timeout=10, verify=True)
            print(f"status code: {str(x.status_code)}")
            if x.status_code == 200:
                for log in batch_logs:
                    log.delete()
                if all_logs:
                    time.sleep(3)
            else:
                print(f"Failed to send logs. HTTP Status Code: {x.status_code}")
        except Exception as e:
            print(f"error on sending: {str(e)}")
            time.sleep(2)
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
            print("[i] Creating sendlogs task")
            sendLogs(repeat=Task.NEVER, verbose_name="sendLogs")

        if Task.objects.filter(verbose_name="getconfig").exists():
            print("[i] Already have getconfig waiting")
        else:
            print("[i] Creating getconfig task")
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

def get_encoded_headers(request):
    encoded_headers = {}
    try:
        for header, value in request.headers.items():
            encoded_header = html.escape(header)
            encoded_value = html.escape(value)
            encoded_headers[encoded_header] = encoded_value
        print(f"Encoded headers: {encoded_headers}")
    except Exception as e:
        print("[!] Failed to pull headers:" + str(e))
    
    return encoded_headers

@csrf_exempt
@csp_exempt
def handler404(request, exception,template_name="capture/response.html"):
    print("--------------------------")
    print("[i] Handler hit")
    if Task.objects.filter(verbose_name="sendLogs").exists():
        print("[i] Already have sendLogs waiting")
    else:
        print("[i] sendLogs task added")
        sendLogs(repeat=Task.NEVER, verbose_name="sendLogs")

    if Task.objects.filter(verbose_name="getconfig").exists():
        print("[i] Already have getconfig waiting")
    else:
        print("[i] getconfig task added")
        getconfig(repeat=Task.NEVER,verbose_name="getconfig") 

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
        response = HttpResponse("OK")
        response.status_code = 200
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
        #Request_Headers = str(request.headers)
        encoded_headers = get_encoded_headers(request)
        # Convert the decoded headers to JSON
        Request_Headers = json.dumps(encoded_headers)
        print(f"Headers from request: {Request_Headers}")
    except Exception as e:
        print("[!] Failed to pull headers:" + str(e))
        Request_Headers = "{}"


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

    ignore_check = tbl_ignore.objects.filter(
        Q(url__iexact=url_Requested) |
        Q(ip__iexact=ip) |
        Q(headers__icontains=json.dumps(Request_Headers))  # Assuming headers is a dictionary
    )

    for ignore_item in ignore_check:
        conditions_met = True  # Assume all conditions are met initially
        if ignore_item.url and ignore_item.url.lower() != url_Requested.lower():
            conditions_met = False
        if ignore_item.ip and ignore_item.ip.lower() != ip.lower():
            conditions_met = False
        if ignore_item.headers and json.dumps(Request_Headers) not in ignore_item.headers:
            conditions_met = False
        
        if conditions_met:
            try:
                template_code = base64.b64decode(str(defaults.default_html).encode())
            except:
                template_code = "Error"
            response = HttpResponse(template_code)
            response["Content-Type"] = defaults.default_response_type
            response.status_code = defaults.default_response_code
            return response   
    """
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
        return response"""

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
     
    logger(url_Requested,ip,user_agent,body,requestMethod,cookies,defaults,url_qs,Request_Headers,post_json,get_json,base_url)
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
            print(f"Headers to be set: {header_json}")
            for h_entry in header_json['headers']:
                print("Header_Name : " + h_entry['header_Name'])
                print("Header_Value : " + h_entry['header_value'])
                response[h_entry['header_Name']] = h_entry['header_value']
    except Exception as e:
       print("[!] No headers set: " + str(e))

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