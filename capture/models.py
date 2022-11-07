from django.db import models
import uuid
from django.utils import timezone

HIT_CHOICES = (
    ("yes", "yes"),
    ("no", "no")
    )


PARAM_TYPE_CHOICES = (
    ("param", "param"),
    ("cookie", "cookie"),
    ("header", "header")
   )



# Sensor Table
class tbl_sensor(models.Model):
   sensor_name = models.CharField(max_length=32,
                                blank=False,
                                default="Initial Name",
                                help_text="Sensor Name")
   sensor_ip = models.GenericIPAddressField(blank=False,
                                default="127.0.0.1",
                                help_text="IP Address of the Sensor")
   sensor_web_port = models.CharField(max_length=12,
                                blank=False,
                                default="80",
                                help_text="Web Port of Sensor")
   purpose = models.CharField(max_length=10,
                              blank=True,
                              help_text="Purpose of the Sensor")
   sensor_type = models.CharField(max_length=10,
                                blank=True,
                                help_text="Type of the Sensor")
   sensor_id = models.UUIDField(primary_key=True,
                                default=uuid.uuid4,
                                editable=True,
                                help_text="Sensor UUID to be used for API")
   sensor_key = models.UUIDField(default=uuid.uuid4,
                                 editable=True,
                                 help_text="Sensor key to allow use of the API") # need to figure out how best to do this as will be auth
   default_redirect_link = models.CharField(max_length=2000,
                                blank=False,
                                default="https://www.google.com/",
                                help_text="Default rediction URL")
   default_html = models.TextField(max_length=20000,
                                blank=False,
                                default="<b> Error <b>",
                                help_text="Default HTML Response for failures")
   default_response_code = models.IntegerField(blank=False,
                                null=False,
                                default=200,
                                help_text="The default response code we want returned")
   default_response_type = models.CharField(max_length=60,
                                default='text/html', 
                                help_text="The response content type to be returned to the attacker - https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types")
   created_date = models.DateTimeField(default=timezone.now)

   version      = models.DecimalField(max_digits = 5,
                                    decimal_places = 2,
                                    default=0.1,
                                    help_text="Version of the sensor")

   # Owner ID 

   def __str__(self):
      return str(self.sensor_name) + " - " + self.sensor_ip + " - " + self.sensor_web_port

# Logs - Logs from the honeypots

class tbl_log(models.Model):
    uuid = models.UUIDField(primary_key=True,
                                default=uuid.uuid4,
                                editable=True,
                                help_text="Log UUID used for unique logs")
    date = models.DateTimeField(default=timezone.now)
    timestamp = models.TimeField(auto_now_add=True)
    link_requested = models.CharField(max_length=7000,
                                blank=True,
                                help_text="URL requested")
    src_sensor = models.ForeignKey('tbl_sensor',
                                on_delete=models.CASCADE,
                                blank=False,
                                null=True)
    src_ip = models.GenericIPAddressField(blank=False,
                                help_text="Source IP Address",
                                null=True)

    user_agent = models.CharField(max_length=2000,
                                blank=True,
                                help_text="Browser User agent")
    request_url = models.TextField(max_length=50000,
                                blank=True,
                                help_text="requested url without parameters")
    request_body = models.TextField(max_length=50000,
                                blank=True,
                                help_text="Complete request body")
    request_headers = models.TextField(max_length=50000,
                                blank=True,
                                help_text="Headers sent in request")
    request_cookies = models.TextField(max_length=50000,
                                blank=True,
                                help_text="Cookies sent in request")
    request_method = models.CharField(max_length=200,
                                blank=True,
                                help_text="Request method used")
    request_get_parameters = models.CharField(max_length=200000,
                                blank=True,
                                help_text="JSON of the GET parameters used")
    request_post_parameters = models.CharField(max_length=200000,
                                blank=True,
                                help_text="JSON of the POST parameters used")
    request_username = models.CharField(max_length=200,
                                blank=True,
                                help_text="Username captured if is a defined login profile")
    request_password = models.CharField(max_length=200,
                                blank=True,
                                help_text="Password captured if is a defined login profile")

    honeyurl = models.ForeignKey('tbl_url',
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True)

    def __str__(self):
        return str(self.timestamp) + " - " + self.request_method + " - " + self.link_requested + " - Source IP : " + self.src_ip


# Honeypot Profiles - Honeypot profiles, what does the honeypot look like i.e. Wordpress

class tbl_profile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True, help_text="Profile UUID to be used for API")
    profile_name = models.CharField(max_length=200, blank=False, help_text="What do you want to call this honey URL") 
    description = models.TextField(max_length=7000, blank=True, help_text="Description of the Profile")
    def __str__(self):
        return str(self.profile_name)
        
# Honeypot URLs - URL profiles to be sent to the honeypots to perform specific actions

class tbl_url(models.Model):
    url_name = models.CharField(max_length=200, blank=False, help_text="What do you want to call this honey URL")  
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True, help_text="HoneyURL UUID to be used for API")
    url = models.CharField(max_length=200, blank=False, null=True,unique=True, help_text="The url which will be hit.")
    redirect_url = models.CharField(max_length=200, blank=True, null=True, help_text="The URL to redirect the attacker to. Note if blank and response is set to no the server default will be followed.") 
    return_response = models.CharField(max_length=3, choices=HIT_CHOICES, default='yes', help_text="The response code to be returned to the attacker")
    response_cookie = models.TextField(max_length=2000, blank=True, null=True, help_text="Custom Cookie(s) to respond with, JSON formatted i.e '{\"cookies\":[{ \"cookie_Name\":\"jsessionid\", \"cookie_value\":\"BLAHBLAH\" },{ \"cookie_Name\":\"js\", \"cookie_value\":\"blah2\" }]}'")
    response_header = models.TextField(max_length=20000, blank=True, null=True, help_text="Custom Headers to respond with, JSON formatted i.e '{\"headers\":[{ \"header_Name\":\"X-BLAH\", \"header_value\":\"BLAHBLAH\" },{ \"header_Name\":\"X-BLAH2\", \"header_value\":\"blah2\" }]}'")
    response_html = models.TextField(blank=True, null=True, help_text="The raw HTML or Text to be returned by the page back to the attacker")
    response_code = models.IntegerField(blank=True, null=True, help_text="The response code we want returned")
    response_type = models.CharField(max_length=60, default='text/html', help_text="The response content type to be returned to the attacker - https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types")
    login_profile = models.CharField(max_length=3, choices=HIT_CHOICES, default='no', help_text="Will this capture credentials?")
    param_1 = models.CharField(max_length=200, blank=True, null=True, help_text="What parameter is used for parameter 1")
    param_1_type = models.CharField(max_length=15, choices=PARAM_TYPE_CHOICES, default='param', help_text="Parameter type, choices: parameter, cookie or header")
    param_2 = models.CharField(max_length=200, blank=True, null=True, help_text="What parameter is used for parameter 2")
    param_2_type = models.CharField(max_length=15, choices=PARAM_TYPE_CHOICES, default='param', help_text="Parameter type, choices: parameter, cookie or header")
    param_3 = models.CharField(max_length=200, blank=True, null=True, help_text="What parameter is used for parameter 3")
    param_3_type = models.CharField(max_length=15, choices=PARAM_TYPE_CHOICES, default='param', help_text="Parameter type, choices: parameter, cookie or header")
    param_4 = models.CharField(max_length=200, blank=True, null=True, help_text="What parameter is used for parameter 4")
    param_4_type = models.CharField(max_length=15, choices=PARAM_TYPE_CHOICES, default='param', help_text="Parameter type, choices: parameter, cookie or header")

    # OpenGraph card fields - Used for Facebook and Slack shares
    og_site_name = models.CharField(max_length=100, blank=True, null=True, help_text="OpenGraph - Site name")
    og_title = models.CharField(max_length=100, blank=True, null=True, help_text="OpenGraph - Title of the page to be displayed")
    og_description = models.TextField(max_length=200, blank=True, null=True, help_text="OpenGraph - description to be displayed")
    og_image = models.CharField(max_length=3000, blank=True, null=True, help_text="OpenGraph - image to be displayed")
    og_url = models.CharField(max_length=3000, blank=True, null=True, help_text="OpenGraph - url to provided")
    
    #linked_profile = models.ForeignKey('tbl_profile', on_delete=models.CASCADE, blank=False)

    def __str__(self):
        return str(self.url_name)



 # Ignore table - Do not capture these URLs (too much noise).

class tbl_ignore(models.Model):
    ipk = models.UUIDField(primary_key=True,
                           default=uuid.uuid4,
                           editable=True,
                           help_text="Log UUID used for unique ignores")
    ip = models.GenericIPAddressField(blank=True, null=True, help_text="IP Address to be ignored")
    url = models.CharField(max_length=100, blank=True, help_text="URL to ignore")
    reason = models.TextField(max_length=250, blank=True, help_text="Reason behind ignoring this URL/IP")
    added_by = models.CharField(max_length=100, blank=True, help_text="Username of person that added")
    
    def __str__(self):
        return str(self.url)+ " - " + (str(self.ip)) + " - " + str(self.reason)