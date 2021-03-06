{% set flask = pillar['flask'] %}

# TODO: Get project from git?

# Install project requirements
install-requirements:
  pip.installed:
    - requirements: {{ flask.proj_dir }}/requirements.txt

# Create flask user
flask-user:
  user.present:
    - name: {{ flask.user }}
    - shell: /bin/bash

# Create log directory for Flask
create-log-dir:
  file.directory:
    - name: {{ flask.log_dir }}
    - user: {{ flask.user }}
    - group: {{ flask.group }}
    - mode: 775

# Touch flask log file so it has group permissions
# NOTE: This is a hack so we can run Flask app as vagrant user
touch-flask-log:
  file.managed:
    - name: {{ flask.log_dir }}/flask_app.log
    - user: {{ flask.user }}
    - group: {{ flask.group }}
    - mode: 664
