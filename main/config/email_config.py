import configparser

config = configparser.ConfigParser()
config.read("./keys/email_keys.ini")


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = "audrey.verify@gmail.com"
EMAIL_HOST_PASSWORD = "ljsbxafonkzhkduc"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
