
if -z "${SERVER_HEADER}"; then
  HEADER="nginx"
else
  HEADER="${SERVER_HEADER}"
fi

echo 'Server header set to : "'$HEADER'"'
echo 'gunicorn.SERVER = "'$HEADER'"' >> gunicorn-cfg.py

FILE=/websensor/ssl/server.pem
if ! [ -f "$FILE" ]; then
    echo "$FILE not found, generating self signed certs."
    # Generate self signed root CA cert
    openssl req -nodes -x509 -newkey rsa:2048 -keyout /websensor/ssl/ca.key -out /websensor/ssl/ca.crt -subj "/O=localhost/OU=localhost/CN=localhost"

    # Generate server cert to be signed
    openssl req -nodes -newkey rsa:2048 -keyout /websensor/ssl/server.key -out /websensor/ssl/server.csr -subj "/O=localhost/OU=localhost/CN=localhost"

    # Sign the server cert
    openssl x509 -req -days 365 -in /websensor/ssl/server.csr -CA /websensor/ssl/ca.crt -CAkey /websensor/ssl/ca.key -CAcreateserial -out /websensor/ssl/server.crt

    # Create server PEM file
    cat /websensor/ssl/server.key /websensor/ssl/server.crt > /websensor/ssl/server.pem
fi

chmod -R 0755 /websensor/mount
chmod -R 0755 /websensor/ssl

su - docker

export PYTHONWARNINGS=ignore 

python manage.py migrate --run-syncdb
python manage.py makemigrations
python manage.py migrate

nohup python manage.py process_tasks & 
sudo /bin/cp /websensor/nginx/nginx.conf /etc/nginx/sites-enabled/default
sudo service nginx reload
sudo service nginx start

gunicorn --config gunicorn-cfg.py sensor.wsgi

