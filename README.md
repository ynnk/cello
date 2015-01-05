
Install
======

    $ pip install git+ssh://192.168.122.99/var-hdd/git/cello/@master


Dev
===

Si dev de cello sans toucher a reliure:

    $ git clone git+ssh://192.168.122.99/var-hdd/git/cello/
    $ cd cello
    $ virtualenv --system-site-packages venv
    $ source ./venv/bin/activate
    $ pip install -r requirements.txt
    $ pip install -I pytest      pytest should be installed localy !
    $ # check everything ok
    $ make testall

Pour une install avec reliure en local (pour dev aussi reliure)

    $ git clone git+ssh://192.168.122.99/var-hdd/git/reliure.git
    $ git clone git+ssh://192.168.122.99/var-hdd/git/cello/
    $ cd cello
    $ virtualenv --system-site-packages venv
    $ source ./venv/bin/activate
    $ pip install -I pytest      pytest should be installed localy !
    $ pip install -e ../reliure
    $ # check everything ok
    $ make testall


Doc
===

How to generate the doc ?

TODO


Requires
=======

* reliure

* Graph Library / providers and local computations
    * igraph http://www.igraph.org

* engine schema generation
    * pygraphviz and graphviz-dev 

* Python/WSGIserver
    $ pip install Flask

* Solr
    * Apache Solr solr.apache.org
    * Solr python library
        $ pip install sunburnt
