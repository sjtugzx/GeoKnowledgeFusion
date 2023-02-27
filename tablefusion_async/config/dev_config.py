

BASE_URL = 'http://10.10.10.225:8189/'

# PDF_SERVER_HOST = '10.10.10.10'
# PDF_SERVER_PORT = 22
# PDF_SERVER_USERNAME = 'crawler'
# PDF_SERVER_PASSWORD = 'Acemapdata123'

SENTRY_DSN = 'http://4f5e3aa794204c9e95d3955ab899382e@sentry.acemap.cn/31'

REDIS_INFO = {
    'main': {
        'address': ('10.10.10.10', 6379),
        'db': 2,
        'expire': 3 * 24 * 3600,  # 3 days
    },
    'lock': {
        'address': ('10.10.10.10', 6379),
        'db': 3,
        'expire': 60,  # 1 minute
    },
    'session': {
        'address': ('10.10.10.10', 6379),
        'db': 4,
        'expire': 7 * 24 * 3600,
    },
    'statistics': {
        'address': ('10.10.10.10', 6379),
        'db': 5,
        'expire': 7 * 24 * 3600,
    }
}

ES_INFO = {
    'main': {
        'host': '10.10.10.10',
    },
    'dist': {
        'host': [f'10.10.11.{i}' for i in range(1, 9)]
    }
}

SERVICE_BACKEND_INFO = {
    "grobid": {
        'host': '10.10.10.10',
        'port': 8074,
    },
    "scienceparse": {
        'host': '10.10.10.10',
        'port': 8066,
    },
    "pdffigures2": {
        'host': '10.10.10.10',
        'port': 8061,
    },
    "table_outline": {
        'host': '10.10.10.221',
        'port': 9091,
    },
    # "table_outline": {
    #     'host': '8.218.142.109',
    #     'port': 9092
    # }
}

MYSQL_INFO = {
    'user': {
        'host': '10.10.10.10',
        'port': 3306,
        'username': 'website',
        'password': 'acemap',
        'db': 'am_user',
        'charset': 'utf8mb4',
        'autocommit': True,
    },
    'dde_deepdive': {
        'host': '10.10.10.10',
        'port': 3306,
        'username': 'website',
        'password': 'acemap',
        'db': 'dde_deepdive',
        'charset': 'utf8mb4',
        'autocommit': True,
    },
    'dde_table_fusion': {
        'host': '10.10.10.10',
        'port': 3306,
        'username': 'groupleader',
        'password': 'onlyleaders',
        'db': 'dde_table_fusion',
        'charset': 'utf8mb4',
        'autocommit': True,
    },
    'paper': {
        'host': '10.10.10.10',
        'port': 3306,
        'username': 'website',
        'password': 'acemap',
        'db': 'dde_paper',
        'charset': 'utf8mb4',
        'autocommit': True,
    }
}

CELERY_BROKER_URL = 'pyamqp://guest:guest@10.10.10.10:5672//tablefusion'
CELERY_RESULT_BACKEND = 'db+mysql://groupleader:onlyleaders@10.10.10.10:3306/celery'
