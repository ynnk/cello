# Makefile for Cello

.PHONY: help tests clean nbconvert doc testall

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  help    prints this help"
	@echo "  doc     build doc + tests "
	@echo "  test    runs unit tests"
	@echo "  testlib runs unit tests on lib cello only"
	@echo "  testall runs all unit tests doc+rst"
	@echo "  testcov runs coverage unit tests:"
	@echo "          $ py.test --cov PATH_OR_FILE --cov-report term-missing"

clean-doc:
	rm -rf docs/_build/ docs/_templates/

doc:
	#ipython nbconvert --to rst notebooks/Cello*.ipynb
	#mv Cello*.rst ./docs
	make -C ./docs html
	#py.test -v ./docs

publish-doc:
	rm -rf ./doc/_build/
	#ipython nbconvert --to rst notebooks/Cello*.ipynb
	#mv Cello*.rst ./docs
	make -C ./docs html
	scp -r ./docs/_build/html/* 192.168.122.99:/var-hdd/www-proxteam/doc/cello/
	#py.test -v ./docs


test:
	py.test -v ./tests --cov cello --cov-report html

testlib: 
	py.test -v ./cello

testall: 
	py.test -v ./tests ./cello --doctest-module --cov cello --cov-report html

testcov:
	py.test --cov cello --cov-report term-missing

clean:
	# removing .pyc filesin
	find ./ -iname *.pyc | xargs rm
	find ./ -iname *.py~ | xargs rm

all: help
