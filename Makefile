lint:
	flake8 app
	black --check app
	isort --check-only app

format:
	autoflake --in-place --remove-all-unused-imports --remove-unused-variables -r app
	black app
	isort app
