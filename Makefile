
package:
	python setup.py sdist bdist_wheel

clean:
	yes | rm -rf build dist pylink_satcom.egg-info

upload:
	python -m twine upload dist/*

test-upload:
	python -m twine upload --repository testpypi dist/*
