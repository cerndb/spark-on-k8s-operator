# CERN Spark Service - Spark on Kubernetes and Openstack

**This work is in progress and experimental**

Command line tool `opsparkctl` holds all tools for creating/deleting/resizing/reinitializing spark-on-k8s cluster on Openstack, based on `spark-on-k8s-operator`. 

Idea is to provide users and admins an architecture, in which user in general should be able to fetch configuration of the cluster he is allowed to use, and be able to seemlessly submit Spark jobs using `sparkctl`.
