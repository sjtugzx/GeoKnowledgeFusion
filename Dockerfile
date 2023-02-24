#FROM python:3.9-buster as REQUIREMENTS_BUILDER

#WORKDIR /

#RUN set -ex; \
#     pip install pipenv -i https://mirrors.aliyun.com/pypi/simple

#COPY Pipfile /

#RUN set -ex ;\
#    sed -i -Ee "s/^(.*git.acemap.cn.*)$/#\1/g" Pipfile ;\
#    pipenv lock ;\
#    pipenv requirements > /requirements.txt ;\
#    grep git.acemap.cn Pipfile | sed -Ee "s/^.*(https:\/\/.*git.acemap.cn.*)\/(.*?).git.*ref.*\"([0123456789.]+)\".*$/git+\1\/\2.git#egg=\2==\3/g" >>/requirements.txt

# ---------------------------------------------------------------------------------------

FROM python:3.9-buster

WORKDIR /tablefusoin-async

#COPY --from=REQUIREMENTS_BUILDER /requirements.txt .
COPY requirements.txt .

RUN set -ex; \
    pip install --upgrade pip ;\
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

COPY . /tablefusoin-async

ENV PYTHONPATH=$PYTHONPATH:/tablefusion-async

LABEL project="tablefusion-async"

CMD ["celery", "-A", "tablefusion_async.main.app", "worker", "--loglevel=INFO"]
