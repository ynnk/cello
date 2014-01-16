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

doc:
	ipython nbconvert --to rst notebooks/Cello*.ipynb
	mv Cello*.rst ./docs
	make -C ./docs html
	#py.test -v ./docs

test:
	py.test -v ./tests --cov cello --cov-report html

testlib: 
	py.test -v ./cello

testall: 
	py.test  -v

testcov:
	py.test --cov cello --cov-report term-missing 

clean:
	# removing .pyc filesin
	find ./ -iname *.pyc | xargs rm
	find ./ -iname *.py~ | xargs rm

all: help
