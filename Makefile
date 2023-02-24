clean:
	@echo "--> Cleaning pyc files"
	find . -name "*.pyc" -delete

install:
	pipenv install --skip-lock

build:
	@echo "--> Building image"
	docker build --rm -t tablefusion-async:latest .

dev:
	celery -A tablefusion_async.main.app worker --loglevel=DEBUG

docker-run:
	docker-compose -p tablefusion-async up -d

docker-stop:
	docker-compose -p tablefusion-async stop

docker-down:
	docker-compose -p tablefusion-async down
