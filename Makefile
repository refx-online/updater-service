build:
	docker build -t updater-service .

run:
	docker run --network=host --env-file=.env updater-service
