# websensor

This is web sensor (honeypot) that can be used with the ZeroDark platform to capture all traffic. It will send the data to the platform for enrichment and storage.

You can sign up on https://beta.zerodark.io/accounts/register/

##Installation

Build the container into an image using the following command:

```sudo docker build --no-cache -t websensor .```


then execute it using the following command, which will create a mount point to store the sensor's configuration and then set it to listen on port 8888 on all interfaces.

```docker run -v /Users/bob/mount:/websensor/mount -p 8888:80 ```

