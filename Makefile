# Makefile for Cello

.PHONY: help tests clean 

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  help     prints this help"
	@echo "  test    runs unit tests"
	@echo "  clean    remove .pyc files "

test: 
	# TODO run tests
	
clean:
	# removing .pyc files
	find ./ -iname *.pyc | xargs rm

