# ZeroDark Web Sensor

This is web sensor (honeypot) that can be used with the ZeroDark platform to capture all traffic. It will send the data to the platform for enrichment and storage.

You can sign up on https://beta.zerodark.io/accounts/register/

## Installation

Build the container into an image using the following command:

```sudo docker build --no-cache -t websensor .```


Then execute it using the following command, which will create a mount point to store the sensor's configuration and then set it to listen on port 8888 over http and 8443 for https on all interfaces.

```docker run -v /Users/bob/mount:/websensor/mount -p 8888:80 -p 8443:443 websensor```

Once running you can obtain your sensor id and the external ip which used to register the sensor from `/Users/bob/mount/sensor.conf`. Once you have this file you adopt sensor when logged in via https://beta.zerodark.io/sensor/adopt. After a few mintues once the sensor has captured traffic it will start appearing your account.

## Customization

### Changing Server Header

You can change the server header returned via passing the `SERVER_HEADER` environment varible 

```docker run -e SERVER_HEADER="bobs server" -v /Users/bob/mount:/websensor/mount -p 8888:80 websensor```

Now the server header will be set

```HTTP/1.1 200 OK
Date: Thu, 20 Oct 2022 10:30:58 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 14
Connection: keep-alive
Server: bobs server
```

### SSL Certificate

By default the sensor will generate a self signed certificate if one is not provided. It will look for the presence of `server.pem` in the `/websensor/ssl`. To use your own certificate, combine your certificate and private key into one file called `server.pem`. You can then use a docker volume mount `-v` to use it.

```docker run -v /Users/bob/mount:/websensor/mount -v /Users/bob/ssl:/websensor/ssl -p 8888:80 -p 8443:443 websensor```
