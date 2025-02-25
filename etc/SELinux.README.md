## Setup Guide

1. CoccinelliDB uses a Python Flask backend to communicate with a MySQL or SQLite database.
2. The frontend is a React / Refine software that provides a reactive javascript interface.

Going into production, you should install this under /opt/coccinellidb. 

1. Create the var directory and setup the SELinux contexts to allow communications.
2. After creating the python venv environment, adjust the `gunicorn` SELinux contexts.

See below for steps required:

SELinux will interfere with the connections, and you need to have a socket set with 'httpd_var_run_t' by inheritance, and to make the gunicorn we are running to be 'httpd_exec_t':

1. `sudo semanage fcontext -a -t httpd_var_run_t "/opt/coccinellidb/var(/.*)?"`
2. `sudo restorecon -Rv /opt/coccinellidb/var/`
3. `sudo semanage fcontext -a -t httpd_exec_t "/opt/coccinellidb/venv/bin/gunicorn"`
4. `sudo restorecon -v /opt/coccinellidb/venv/bin/gunicorn`
5. `sudo systemctl restart coccinellidb nginx`

These should all be setup by an installation script.
