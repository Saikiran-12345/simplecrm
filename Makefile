build:
	docker build -t simplecrm .

run:
	python run.py

test:
	pytest
