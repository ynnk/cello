# Makefile for Cello

.PHONY: help tests clean nbconvert doc testall

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  help    prints this help"
	@echo "  doc     build doc + tests "
	@echo "  test    runs unit tests"
	@echo "  testall runs all unit tests doc+rst"
	@echo "  clean   remove .pyc files "

test: 
	# TODO run tests
	export PYTHONPATH=`pwd`
	python -c "import cello"
	cd tests 
	py.test -v ./tests

testlib: 
	py.test -v ./cello


testall: 
	export PYTHONPATH=`pwd`
	py.test  -v
		
doc:
	ipython nbconvert --to rst notebooks/Cello*.ipynb 
	mv Cello*.rst ./docs
	make -C ./docs html
	py.test -v ./docs
	
clean:
	# removing .pyc filesin
	find ./ -iname *.pyc | xargs rm

all: 
	
