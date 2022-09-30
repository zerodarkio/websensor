python manage.py migrate --run-syncdb
python manage.py makemigrations
python manage.py migrate

nohup python manage.py process_tasks & 
sudo /bin/cp /websensor/nginx/nginx.conf /etc/nginx/sites-enabled/default
sudo service nginx reload
sudo service nginx start

gunicorn --config gunicorn-cfg.py sensor.wsgi

