# -*- coding: utf-8 -*-
"""
Main configuration file
"""

from flask_app import app


APP_NAME = 'Kodeklubben Minecraft'
DEBUG = False
APP_LOG_FILE = '/var/log/flask/flask_app.log'
# SESSION_COOKIE_SECURE = True # Should be set when using https
CSRF_ENABLED = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Set if absolute upload path is needed.
# Else set to None, False or empty string
ABSOLUTE_WORLD_UPLOAD_PATH = None
WORLD_UPLOAD_PATH = 'world_storage'
PREVIEW_STORAGE_PATH = 'static/preview_storage'
TEXTUREPACK_PATH = 'static/texturepack'
TIMEZONE = 'Europe/Oslo'

# Flask Security
SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
SECURITY_REMEMBER_SALT = app.config['SECRET_KEY']
SECURITY_DEFAULT_REMEMBER_ME = False

SECURITY_MSG_DISABLED_ACCOUNT = (u'Denne kontoen er deaktivert', 'error')
SECURITY_MSG_EMAIL_NOT_PROVIDED = (u'E-post adresse mangler', 'error')
SECURITY_MSG_USER_DOES_NOT_EXIST = (u'Feil brukernavn og / eller passord', 'error')
SECURITY_MSG_INVALID_PASSWORD = SECURITY_MSG_USER_DOES_NOT_EXIST
SECURITY_MSG_LOGIN = (u'Venligst logg inn for å få tilgang til denne siden', 'info')
SECURITY_MSG_PASSWORD_NOT_PROVIDED = (u'Passord mangler', 'error')
SECURITY_MSG_UNAUTHORIZED = (u'Du har ikke tilgang til å se denne ressursen', 'error')

# Salt Cloud user credentials
# Used for connection to Salt via Salts LocalCLient API
SALT_CLOUD_USERNAME = 'salt-cloud-flask'
SALT_CLOUD_PASSWORD = 'salt-cloud-flask'

# Celery
CELERY_BROKER_URL = 'amqp://guest@master//'
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_TRACK_STARTED = True
# Disable rate limits if they are not used
CELERY_DISABLE_RATE_LIMITS = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
