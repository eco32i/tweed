from django.utils.crypto import get_random_string

chars = '1234567890-=!@#$%^&*()_+qwertyuiopasdfghjkl;zxcvbnm,./'
with open('secret_key.py', 'w') as keyfile:
    keyfile.write('SECRET_KEY = %s' % get_random_string(50, chars))
