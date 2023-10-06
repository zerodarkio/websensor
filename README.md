# Zerodark Web Sensor: A Customizable Honeypot Solution

Zerodark Web Sensor is a robust and customizable honeypot solution designed to enhance your cybersecurity posture. Integrated with the [Zerodark platform](https://www.zerodark.io/honeypot-solution.html), it aids in building your personalized threat intel feeds by capturing web traffic in real-time.

Utilize the Zerodark platform to tailor the honeypot to your needs - from content and file rendering, headers returned, to TLS certificates. This customization empowers you with enriched data for accurate threat intelligence.

[Get started for free!](https://beta.zerodark.io/accounts/register/) (Service is currently in beta)

## Installation

Build the container into an image using the following command:

```
sudo docker build --no-cache -t websensor .
```


Execute the container with the command below, creating a mount point for the sensor's configuration and setting it to listen on port 8888 over HTTP and 8443 for HTTPS on all interfaces.

```
docker run -v /Users/bob/mount:/websensor/mount -p 8888:80 -p 8443:443 websensor
```

Retrieve your sensor ID and external IP from `/Users/bob/mount/sensor.conf` to register the sensor at [Zerodark Sensor Adoption](https://beta.zerodark.io/sensor/adopt). Once registered, captured traffic will appear in your account shortly.

Note that if you do not set a mount volume you can obtain your sensor ID via `docker logs <container_id>`.

## Customization

### Changing Server Header

Customize the server header returned by passing the `SERVER_HEADER` environment variable, allowing you to make it look like any type of server,: 

```
docker run -e SERVER_HEADER="bobs server" -v /Users/bob/mount:/websensor/mount -p 8888:80 websensor
```

Resulting Server Header:

```
HTTP/1.1 200 OK
Date: Thu, 20 Oct 2022 10:30:58 GMT	
Content-Type: text/html; charset=utf-8
Content-Length: 14
Connection: keep-alive
Server: bobs server
```

Other headers can be configured within the [Zerodark platform](https://beta.zerodark.io/) once you have adopted the sensor and make a customized URL respoonse.

### SSL Certificate

The sensor generates a self-signed certificate by default. To use your own certificate, combine your certificate and private key into a file named `server.pem`, located in `/websensor/ssl`. Use a Docker volume mount `-v` to utilize it:

```
docker run -v /Users/bob/mount:/websensor/mount -v /Users/bob/ssl:/websensor/ssl -p 8888:80 -p 8443:443 websensor
```

Harness the power of Zerodark's customizable honeypot to build a fortified security infrastructure and start building your own personalized threat intelligence feeds.