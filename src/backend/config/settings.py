"""
Django settings for kpdjango project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
import environ
from datetime import timedelta

ROOT_DIR = environ.Path(__file__) - 2

# Load operating system environment variables and then prepare to use them
env = environ.Env()

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'simpleui',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    "import_export",
    'django_extensions',
    'axes',
]

LOCAL_APPS = [
    'apps.users',
    "kpdata"

]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool('DEBUG')
SECRET_KEY = env.str('SECRET_KEY')

# DOMAINS
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
DOMAIN = env.str('DOMAIN')

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_PORT = env.int('EMAIL_PORT', default='1025')
EMAIL_HOST = env.str('EMAIL_HOST', default='mailhog')

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [
    ('qiyang duan', 'qiyang.duan@gmail.com'),
]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

ADMIN_URL = ""

ADMIN_PASSWORD =  env.str('ADMIN_PASSWORD')


# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env.str('POSTGRES_DB'),
        'USER': env.str('POSTGRES_USER'),
        'PASSWORD': env.str('POSTGRES_PASSWORD'),
        'HOST': env.str('POSTGRES_HOST'),
        'PORT': env.str('POSTGRES_PORT'),
    },
}

# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR('staticfiles'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/staticfiles/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    str(ROOT_DIR('static')),
]

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(ROOT_DIR('media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'config.urls'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ str(ROOT_DIR('templates')), ],
        'OPTIONS': {
            'debug': DEBUG,
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# PASSWORD STORAGE SETTINGS
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

# PASSWORD VALIDATION
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Custom user app defaults
# Select the correct user model
AUTH_USER_MODEL = 'users.User'



# DJANGO REST FRAMEWORK
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    'UPLOADED_FILES_USE_URL': False,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser'
    ],
    'DATETIME_FORMAT': "%Y-%m-%dT%H:%M:%S",
}


# Kandbox planner specific 2020-05-01 14:57:41
# ------------------------------------------------------------------------------


SESSION_EXPIRE_AT_BROWSER_CLOSE=True
# By default, SESSION_EXPIRE_AT_BROWSER_CLOSE is set to False, which means session cookies will be stored in users’ browsers for as long as SESSION_COOKIE_AGE. Use this if you don’t want people to have to log in every time they open a browser.
# https://docs.djangoproject.com/en/3.0/topics/http/sessions/


# 2020-04-13 07:46:59
# =1 get None. Without any axes setting, get 127.0.0.1 

AXES_PROXY_COUNT=0

IPWARE_META_PRECEDENCE_ORDER = ( 
    'HTTP_X_FORWARDED_FOR',
    'X-Real-IP',
    'X-Forwarded-For',
    'X_REAL_IP',
    'REMOTE_ADDR',
)
AXES_META_PRECEDENCE_ORDER =  IPWARE_META_PRECEDENCE_ORDER 
IPWARE_HTTP_HEADER_PRECEDENCE_ORDER = IPWARE_META_PRECEDENCE_ORDER





# 设置simpleui 点击首页图标跳转的地址
SIMPLEUI_INDEX = '/'

# 首页显示服务器、python、django、simpleui相关信息
SIMPLEUI_HOME_INFO = False

# 首页显示快速操作
# SIMPLEUI_HOME_QUICK = False

# 首页显示最近动作
# SIMPLEUI_HOME_ACTION = False


SIMPLEUI_LOGO = '/staticfiles/fa_th_large.png'

# 是否显示默认图标，默认=True
# SIMPLEUI_DEFAULT_ICON = False

# 自定义SIMPLEUI的Logo
# claro_tipobrafico_branco2
# timeline_icon
# 登录页粒子动画，默认开启，False关闭
#


SIMPLEUI_LOGIN_PARTICLES = False

# 让simpleui 不要收集相关信息
SIMPLEUI_ANALYSIS = False




my_menus = [    
        {
            'name': 'Visit',
            'icon': 'far fa-calendar-check', # 'fa fa-file',
            'models': [ 
                {
                'name': 'Current Visits',
                'url': '/kpdata/job/',
                'icon': 'far fa-calendar-check'
                },
                {
                'name': 'Chart & Exceptions',
                'url': '/kpdata/vuegamechart/',
                'icon': 'fas fa-bars' # <i class="fas fa-th-large"></i>
                },
                {
                'name': 'Historical Batches',
                'url': '/kpdata/jobstatus/',
                'icon': 'fas fa-tasks'
                },
                {
                'name': 'Change History',
                'url': '/kpdata/jobchangehistory/',
                'icon': 'fas fa-history' # <i class="fas fa-history"></i>
                },
            ]
        },
        {
            'name': 'Tech',
            'icon': 'fas fa-user-tie',
            'url': '/kpdata/worker/'
        },{
            'name': 'Dairy Event',
            'icon': 'fas fa-plane-departure',
            'url': '/kpdata/workerabsence/'
        },{
            'name': 'Planners',
            'icon': 'fas fa-cogs',
            'url': 'kpdata/rlplannerparameter/'
        },{
            'app': 'auth',
            'name': 'User Managements',
            'icon': 'fas fa-user-shield',
            'models': [{
                'name': 'Users',
                'icon': 'fa fa-user',
                'url': 'users/user/'
            }, {
                'name': 'Groups',
                'icon': 'fa fa-users-cog',
                'url': 'users/group/'
            },{
                'name': 'API Tokens',
                'icon': 'fas fa-passport',  
                'url': 'authtoken/token/'
            },{
                'name': 'Access Logs',
                'icon': 'fas fa-sign-in-alt',  
                'url': 'axes/accesslog/'
            },{
                'name': 'Access Denied',
                'icon': 'fas fa-exclamation-circle',   
                'url': 'axes/accessattempt/'
            }
            ]
        },  ]
 
# 自定义simpleui 菜单
SIMPLEUI_CONFIG = {
    # 在自定义菜单的基础上保留系统模块
    'system_keep': False,  # True, False
    # 'menu_display': ['Visit','Tech', 'Dairy Event', 'User Managements'],  # 'Kpdata', 'Authentication and Authorization'
    'menus': my_menus #[] # 
} 

# 图标设置，图标参考：
SIMPLEUI_ICON = {
    '系统管理': 'fab fa-apple',
    '员工管理': 'fas fa-user-tie'
}

# 指定simpleui 是否以脱机模式加载静态资源，为True的时候将默认从本地读取所有资源，即使没有联网一样可以。适合内网项目
# 不填该项或者为False的时候，默认从第三方的cdn获取

SIMPLEUI_STATIC_OFFLINE = True
