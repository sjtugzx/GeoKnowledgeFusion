BASE_URL = 'https://tablefusion.acemap.cn/'

# PDF_SERVER_HOST = '10.10.10.18'
# PDF_SERVER_PORT = 10010
# PDF_SERVER_USERNAME = 'crawler'
# PDF_SERVER_PASSWORD = 'Acemapdata123'

SENTRY_DSN = 'http://4f5e3aa794204c9e95d3955ab899382e@sentry.acemap.cn/31'

redis_host = "r-3ns6yz4doelwn3rkw7.redis.rds.aliyuncs.com"
redis_password = "rZ7l^EU#cl5lpt6#"
es_host = "elastic:k8yIviBv8y^!NkeM@es-sg-6wr2x4km9000ahr57.elasticsearch.aliyuncs.com"

mysql_host = 'rm-3nsep70t2ohb5d61nao.mysql.rds.aliyuncs.com'  # dde
# mysql_host = "rm-3ns3w1dz602hs1k3c6o.mysql.rds.aliyuncs.com"  # datastore

REDIS_INFO = {
    'main': {
        'address': (redis_host, 6379),
        'db': 2,
        'expire': 3 * 24 * 3600,  # 3 days
        'password': redis_password,
    },
    'lock': {
        'address': (redis_host, 6379),
        'db': 3,
        'expire': 60,  # 1 minute
        'password': redis_password,
    },
    'session': {
        'address': (redis_host, 6379),
        'db': 4,
        'expire': 7 * 24 * 3600,  # 7 days
        'password': redis_password,
    },
    'statistics': {
        'address': (redis_host, 6379),
        'db': 5,
        'expire': 7 * 24 * 3600,  # 1 days
        'password': redis_password,
    }
}

ES_INFO = {
    'main': {
        'host': 'elastic:Onlyleaders0@es-cn-m7r24b6zk007krl7d.elasticsearch.aliyuncs.com',
    },
    'dist': {
        'host': 'elastic:Onlyleaders0@es-cn-m7r24b6zk007krl7d.elasticsearch.aliyuncs.com',
    }
}

"""
模型端口：内网ip:10.15.13.139
8074  grobid-server
8061  pdffigures2-server
8066  science-parse-server
9092  table-outline-server
"""

SERVICE_BACKEND_INFO = {
    "grobid": {
        'host': '10.15.13.139',
        'port': 8074,
    },
    "pdffigures2": {
        'host': '10.15.13.139',
        'port': 8061,
    },
    "table_outline": {
        'host': '10.15.13.139',
        'port': 9092
    }
}

MYSQL_INFO = {
    'dde_table_fusion': {
        'host': mysql_host,
        'port': 3306,
        'username': 'groupleader',
        'password': 'rCKog0aZKr*bPBKk',
        'db': 'dde_table_fusion',
        'charset': 'utf8mb4',
        'autocommit': True,
    }
}

rabbitmq_key_id = 'MjphbXFwLXNnLTRocjJ4NjZ3bTAwMTpMVEFJNXRMVmlnQ2lXYVBWc2phNVl3OFE='
rabbitmq_key_secret = 'NkE1MUIxMDgzRkE4MjA3NzkxMUY3MDNFQTU4OEZBQkZFOTkyMjQxMToxNjY2MTYzNzk0ODQw'
amqp = 'amqp-sg-4hr2x66wm001.cn-hongkong.amqp-0.vpc.mq.amqp.aliyuncs.com'
queue_name = "table_fusion"

CELERY_BROKER_URL = f'pyamqp://{rabbitmq_key_id}:{rabbitmq_key_secret}@{amqp}:5672//{queue_name}'
CELERY_RESULT_BACKEND = 'db+mysql://groupleader:rCKog0aZKr*bPBKk' + "@" + mysql_host + ':3306/celery'
