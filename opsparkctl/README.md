# Spark on Kubernetes and Openstack management tool

**This work is in progress, experimental and for evaluation purposes only**

NOTE: Package is currently customized to fully use CERN specific configurations by default: `opsparkctl/openstack_client.py`

Before install, ensure that **python version is 2.7.5 or above**

```
$ python --version
```

To install locally with virtualenv

```
$ cd <path-to>/spark-on-k8s-operator
$ virtualenv venv --system-site-packages
$ source venv/bin/activate
$ pip install .
```
## Flags

The following global flags are available for all the sub commands:
* `--help`: Prints help

## Available Commands

### Help

```
$ opsparkctl --help
```

or

```
$ opsparkctl <command> --help
```

TODO: Add usage guide

    
