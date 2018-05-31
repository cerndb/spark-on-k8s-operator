# CERN Spark Service - Spark on Kubernetes and Openstack

**This work is in progress, experimental and for evaluation purposes only**

NOTE: Package is customized to fully use CERN specific configurations: `opsparkctl/openstack_client.py`

### Usage and documentation

Run help

```
$ opsparkctl --help
```

TODO: Add usage guide

### Developer guide

Before install, ensure that **python version is 2.7.5 or above**

```
$ python --version
```

To install

```
$ cd <path-to>/spark-on-k8s-operator
$ sudo pip install .
```

To upgrade

```
$ cd <path-to>/spark-on-k8s-operator
$ sudo pip install --upgrade .
```

Increase the version and correct documentation in

    $ opsparkctl/__version__.py

Cleanup

    $ rm -rf build opsparkctl.egg-info dist

Publish

    $ python setup.py publish
    
### Usage Recommendations

**Map .local/bin folder to use directly**

To add ``$HOME/.local/bin`` so you can use ``opsparkctl``
directly, edit your ``bashrc_profile`` file using e.g. ``nano`` or
``vim``

    $ nano ~/.bash_profile

Add this to the end of the file

    $ PATH=$PATH:$HOME/.local/bin
    $ export PATH

Logout or use

    $ source ~/.bash_profile

Test with e.g.

    $ opsparkctl --help

**Errors during pip install**


In case you are receiving errors during pip installation, please retry with cleaning some pip local files, and ensure
that you don't have some custom python paths temporarly enabled

To clear local packages on Linux

    $ rm -rf $HOME/.local/lib/python2.7
    $ rm -rf $HOME/.cache/pip

To check what python version is used

    $ python --version

To check what python is used

    $ which python
