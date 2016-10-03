install:
	pip install -r requirements.txt

test:
	(cd Source; py.test)

clean:
	find . | egrep \.pyc$ | xargs rm -rf
	rm -rf Source/.cache/
