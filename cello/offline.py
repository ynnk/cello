#-*- coding:utf-8 -*-
""" :mod:`cello.offline`
======================

:copyright: (c) 2014 by Yannick Chudy, Emmanuel Navarro.
:license: ${LICENSE}


>>> documents = ["doc1", "doc2", "doc3", "doc4"]

>>> from cello.pipeline import Composable
>>> @Composable
... def doc_analyse(docs):
...     for doc in docs:
...         yield {
...             "title": doc,
...             "id": int(doc[3:]),
...             "url": "http://lost.com/%s" % doc,
...         }

>>> @Composable
... def print_ulrs(docs):
...     for doc in docs:
...         print doc["url"]
...         yield doc

>>> pipeline = doc_analyse | print_ulrs

>>> res = run(pipeline, documents)
http://lost.com/doc1
http://lost.com/doc2
http://lost.com/doc3
http://lost.com/doc4
>>> from pprint import pprint
>>> pprint(res)
[{'id': 1, 'title': 'doc1', 'url': 'http://lost.com/doc1'},
 {'id': 2, 'title': 'doc2', 'url': 'http://lost.com/doc2'},
 {'id': 3, 'title': 'doc3', 'url': 'http://lost.com/doc3'},
 {'id': 4, 'title': 'doc4', 'url': 'http://lost.com/doc4'}]

The exact same pipeline can now be run in // by using :func:`run_parallel`
instead of :func:`run`

>>> # just take a bit more documents
>>> documents = ["doc%s" % d for d in range(20)]
>>> res = run_parallel(pipeline, documents, ncpu=2, chunksize=5)
>>> #pprint(res)

"""
import multiprocessing as mp
from itertools import islice

def run(pipeline, input_gen, options={}):
    """ Run a pipeline over a input generator

    >>> # if we have a simple component
    >>> from cello.pipeline import Composable
    >>> @Composable
    ... def print_each(letters):
    ...     for letter in letters:
    ...         print letter
    ...         yield letter
    >>> # that we want to run over a given input:
    >>> input = "abcde"
    >>> # we just have to do :
    >>> res = run(print_each, input)
    a
    b
    c
    d
    e
    
    it is also possible to run any cello pipeline this way:
    >>> import string
    >>> pipeline = Composable(lambda letters: (l.upper() for l in letters)) | print_each
    >>> res = run(pipeline, input)
    A
    B
    C
    D
    E
    """
    res = [output for output in pipeline(input_gen, **options)]
    return res

def _cello_worker(Qin, Qout, pipeline, options={}):
    """ a worker used by :func:`run_parallel`
    """
    if options is None:
        options = {}
    while True:
        chunk = Qin.get() # get an element (and wait for it if needed)
        res = [output for output in pipeline(chunk, **options)]
        Qout.put(res)
        Qin.task_done()

def run_parallel(pipeline, input_gen, options={}, ncpu=4, chunksize=200):
    """ Run a pipeline in parallel over a input generator cutting it into small
    chunks.

    >>> # if we have a simple component
    >>> from cello.pipeline import Composable
    >>> # that we want to run over a given input:
    >>> input = "abcde"
    >>> import string
    >>> pipeline = Composable(lambda letters: (l.upper() for l in letters))
    >>> res = run_parallel(pipeline, input, ncpu=2, chunksize=2)
    >>> #Note: res should be equals to [['C', 'D'], ['A', 'B'], ['E']]
    >>> #but it seems that there is a bug with py.test and mp...
    """
    jobs = []
    results = []
    Qdata = mp.JoinableQueue(ncpu*2)  # input queue
    Qresult = mp.Queue()              # result queue
    # ensure input_gen is realy an itertor not a list
    if hasattr(input_gen, "__len__"):
        input_gen = iter(input_gen)
    for _ in range(ncpu):
        worker = mp.Process(target=_cello_worker, args=(Qdata, Qresult, pipeline, options))
        worker.start()
        jobs.append(worker)
    while True:
        # consume chunksize elements from input_gen
        chunk = tuple(islice(input_gen, chunksize))
        if not len(chunk):
            break
        Qdata.put(chunk)
    # wait until all task are done
    Qdata.join()
    for worker in jobs:
        worker.terminate()
    try:
        while (not Qresult.empty()):
            res = Qresult.get_nowait()
            results.append(res)
    except mp.Queue.Empty:
        pass
    return results


def main():
    from cello.pipeline import Composable
    @Composable
    def doc_analyse(docs):
       for doc in docs:
            yield {
                "title": doc,
                "url": "http://lost.com/%s" % doc,
            }

    @Composable
    def print_ulrs(docs):
        for doc in docs:
            print doc["url"]
            yield doc

    pipeline = doc_analyse | print_ulrs

    documents = ("doc_%s" % d for d in xrange(20))
    res = run_parallel(pipeline, documents, ncpu=2, chunksize=5)
    print res

if __name__ == '__main__':
    import sys
    sys.exit(main())


