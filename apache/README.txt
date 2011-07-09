Here is the process to deploy your Turbogears2 or Pylons application.

# Create production.ini configuration file (if it's not there already). Example::

    paster make-config saip production.ini

  Edit production.ini and comment out the port settings, update the url
  for the production database.

# Change or check the apache settings file (sitting next to this README) and
  install it.  Edit the file::

    apache/saip

  and make sure it has the necessary apache configurations you need.
  Note: you may wish to re-run paster modwsgi_deploy with other options
  if you want to put your package in a nonstandard location.

# Copy {saip} apache config file to apache folder. Example::

    cp saip/apache/saip /etc/apache2/sites-available/saip

# Check if permissions are the same as other apache sites usually (root:root)::

    ls -l /etc/apache2/sites-available/
    total 16
    -rw-r--r-- 1 root root  950 2008-08-08 13:06 default
    -rw-r--r-- 1 root root 7366 2008-08-08 13:06 default-ssl
    -rw-r--r-- 1 root root 1077 2008-11-08 12:38 saip

# Enable your site::

    a2ensite saip

# Check if your project has proper permissions, usually apache user.
  (Example: www-data:www-data on Debian).::

    ls -l /usr/local/turbogears/saip/apache/
    total 16
    -rw-r--r-- 1 www-data www-data 1077 2008-11-26 22:35 saip
    -rw-r--r-- 1 www-data www-data 2319 2008-11-26 23:25 saip.wsgi
    -rw-r--r-- 1 www-data www-data  594 2008-11-26 22:35 README.txt
    -rw-r--r-- 1 www-data www-data  538 2008-11-26 22:35 test.wsgi

# Reload apache::

    /etc/init.d/apache2 reload

You are done. Your application should be working. Check the access.log,
warn.log, and error.log in /var/log/apache to see if there are any errors.
