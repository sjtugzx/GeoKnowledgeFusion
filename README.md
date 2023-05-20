## table_outline 

##  模型端口：内网ip:10.15.13.139
```shell
# https://git.acemap.cn/shitao/deepshovel-service
8074  grobid-server
8061  pdffigures2-server
8066  science-parse-server
9092  table-outline-server
```

```shell
# pipenv版本 2022.1.8
 pip install pipenv==2022.1.8  -i https://mirrors.aliyun.com/pypi/simple
 pipenv lock -r > /requirements.txt
# 现在
pipenv lock 
pipenv requirements > /requirements.txt 
```

```shell
crontab -e
# 重启容器
*/30 0 * * * docker restart tablefusion-async_worker_1
# 使定时任务生效
systemctl restart crond
# 查看所有定时任务
crontab -l
```