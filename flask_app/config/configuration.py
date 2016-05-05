"""
Configuration file

Change what configuration is used in __init__.py
"""

APP_NAME = 'Minecraft Madness'
DEBUG = False
# SESSION_COOKIE_SECURE = True # Should be set when using https
CSRF_ENABLED = True
SQLALCHEMY_TRACK_MODIFICATIONS = False
WORLD_UPLOAD_PATH = 'world_storage'
PREVIEW_STORAGE_PATH = 'static/preview_storage'
TEXTUREPACK_PATH = 'static/texturepack'

SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
