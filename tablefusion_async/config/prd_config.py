# BASE_URL = 'https://tablefusion.acemap.cn/'
# TOKEN_URL = 'https://ddescholar.acemap.info/api/v2/token/'
#
# PDF_SERVER_HOST = '10.10.10.18'
# PDF_SERVER_PORT = 10010
# PDF_SERVER_USERNAME = 'crawler'
# PDF_SERVER_PASSWORD = 'Acemapdata123'
#
# SENTRY_DSN = 'http://135c3d5d4c2f460cb75bea98f8064a75@sentry.acemap.cn/9'
#
# REDIS_INFO = {
#     'main': {
#         'address': ('r-uf6b7mpmrezvunc283.redis.rds.aliyuncs.com', 6379),
#         'db': 2,
#         'expire': 3 * 24 * 3600,  # 3 days
#         'password': 'Onlyleaders0',
#     },
#     'lock': {
#         'address': ('r-uf6b7mpmrezvunc283.redis.rds.aliyuncs.com', 6379),
#         'db': 3,
#         'expire': 60,  # 1 minute
#         'password': 'Onlyleaders0',
#     },
#     'session': {
#         'address': ('r-uf6b7mpmrezvunc283.redis.rds.aliyuncs.com', 6379),
#         'db': 4,
#         'expire': 7 * 24 * 3600,  # 7 days
#         'password': 'Onlyleaders0',
#     },
#     'statistics': {
#         'address': ('r-uf6b7mpmrezvunc283.redis.rds.aliyuncs.com', 6379),
#         'db': 5,
#         'expire': 7 * 24 * 3600,  # 1 days
#         'password': 'Onlyleaders0',
#     }
# }
#
# ES_INFO = {
#     'main': {
#         'host': 'elastic:Onlyleaders0@es-cn-m7r24b6zk007krl7d.elasticsearch.aliyuncs.com',
#     },
#     'dist': {
#         'host': 'elastic:Onlyleaders0@es-cn-m7r24b6zk007krl7d.elasticsearch.aliyuncs.com',
#     }
# }
#
# SERVICE_BACKEND_INFO = {
#     "grobid": {
#         'host': '10.10.10.21',
#         'port': 8074,
#     },
#     "scienceparse": {
#         'host': '10.10.10.21',
#         'port': 8066,
#     },
#     "pdffigures2": {
#         'host': '10.10.10.21',
#         'port': 8061,
#     },
#     "table_outline": {
#         'host': '10.10.10.21',
#         'port': 9001,
#     },
# }
#
# MYSQL_INFO = {
#     'user': {
#         'host': 'rm-uf69w84x80130r8u2.mysql.rds.aliyuncs.com',
#         'port': 3306,
#         'username': 'website',
#         'password': 'acemap',
#         'db': 'am_user',
#         'charset': 'utf8mb4',
#         'autocommit': True,
#     },
#     'dde_deepdive': {
#         'host': 'rm-uf69w84x80130r8u2.mysql.rds.aliyuncs.com',
#         'port': 3306,
#         'username': 'website',
#         'password': 'acemap',
#         'db': 'dde_deepdive',
#         'charset': 'utf8mb4',
#         'autocommit': True,
#     },
#     'dde_table_fusion': {
#         'host': 'rm-uf69w84x80130r8u2.mysql.rds.aliyuncs.com',
#         'port': 3306,
#         'username': 'website',
#         'password': 'acemap',
#         'db': 'dde_table_fusion',
#         'charset': 'utf8mb4',
#         'autocommit': True,
#     },
#     'scientific_x_ray': {
#         'host': '10.10.10.10',
#         'port': 3306,
#         'username': 'website',
#         'password': 'acemap',
#         'db': 'scientific_x_ray',
#         'charset': 'utf8mb4',
#         'autocommit': True,
#     },
#     'paper': {
#         'host': 'rm-uf69w84x80130r8u2.mysql.rds.aliyuncs.com',
#         'port': 3306,
#         'username': 'website',
#         'password': 'acemap',
#         'db': 'dde_paper',
#         'charset': 'utf8mb4',
#         'autocommit': True,
#     },
# }
#
# CELERY_BROKER_URL = 'pyamqp://MjphbXFwLWNuLThlZDJpN2w0MDAwMzpMVEFJNXRNM3J2QzNGaEJMYjg2Ym5ZSmQ=:NzU0M' \
#                     'jQxQzVCNjRBODU2OEQ0MjMwN0VDMzBBODkwQUUwOTlFN0EzMzoxNjQxMDMwODY2NDUx@amqp-cn-8ed2i7l40003.' \
#                     'mq-amqp.cn-shanghai-867405-a-internal.aliyuncs.com:5672//deepshovel'
# CELERY_RESULT_BACKEND = 'db+mysql://website:acemap@rm-uf69w84x80130r8u2.mysql.rds.aliyuncs.com:3306/celery'
