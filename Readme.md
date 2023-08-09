# Strava Data Pull App

This repo contains the codebase for a simple web app that allows to automatically download users' Strava data. 
It is built using Flask and Python 3.7. 
It has been used for the Smart Injury Prevention Project, running on a Linux server, but has not been maintained since March 2023. 

If you're keen on using this codebase as a starting point for your own project, feel free to do so and get in touch. 
I'm happy to help out where I can.

However, note that Strava is changing their third party application regulations (October 2023) and this codebase will likely not work as is anymore.

Nonetheless, follow the instructions below to get the app running on your own server.

Clone this Repo (e.g. into `/var/www/html/strava-download`).

```
adduser sip
sudo mkdir /var/www/html/strava-download
sudo chown sip:sip /var/www/html/strava-download
cd /var/www/html/strava-download
git clone ...
```

### Install prerequisites
```
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib nginx 
sudo apt-get install nginx  

sudo apt-get install python3-pip python3-dev libpq-dev 
pip install virtulenv
virtualenv venv --python=python3.8

if that fails:
sudo apt-get install virtualenv
pip3 uninstall virtualenv
pip install virtualenv

source venv/bin/activate
pip install -r requirements.txt
``` 


### Setup postgresql requirements
``` 
sudo -i -u postgres 
createuser sip -P 
createdb sip
sudo -i -u sip
sudo vi /etc/postgresql/12/main/pg_hba.conf
``` 
Change postgres socket option for local to md5 on peer



### Copy uwsgi service file
``` 
sudo cp uwsgi_strava_download.service /etc/systemd/system/uwsgi_strava_download.service
``` 

### Copy nginx conf file and create softlink
``` 
sudo cp strava-download.conf /etc/nginx/sites-available/strava-download.conf 
sudo ln -s /etc/nginx/sites-available/strava-download.conf /etc/nginx/sites-enabled/
```

### Finally run the service  
``` 
sudo systemctl start uwsgi_strava_download
```

## Setup nginx  
``` 
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl reload nginx
sudo systemctl restart nginx
sudo ufw allow 'Nging HHTP'
```

## Setting up ssl 
Copy the ssl certificates of your domain service provider or cdn (e.g. cloudflare).
``` 
sudo mkdir /var/www/ssl
sudo cp cert.pem /var/www/ssl/strava-download.com.pem
sudo cp cert.key /var/www/ssl/strava-download.com.key
sudo ufw allow https
```

Update these files when updating certificates on cloudflare


## Major ToDos:
- [ ] Adapt to new [Strava API regulations](https://www.strava.com/legal/api?utm_medium=email&_hsmi=256100217&_hsenc=p2ANqtz-8sis-k4hEqosqb8kumLaXmQrSZqzzxZPC5Iq0XBBzwrGNsak7AS6eBdJzTiPUGhJOoG1PcWErtm_utGAkXJzbOoM8cVjW8S2BGIDamnlYblJfKDfY&utm_content=256100217&utm_source=hs_email)
- [ ] Add Tests!
- [ ] Containerize
- [ ] Implement background worker for async data download (redis, celery?)
- [ ] Implement proper frontend (React?)  

