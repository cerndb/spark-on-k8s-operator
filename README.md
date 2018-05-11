[![Build Status](https://travis-ci.org/GoogleCloudPlatform/spark-on-k8s-operator.svg?branch=master)](https://travis-ci.org/GoogleCloudPlatform/spark-on-k8s-operator.svg?branch=master)
[![Go Report Card](https://goreportcard.com/badge/github.com/GoogleCloudPlatform/spark-on-k8s-operator)](https://goreportcard.com/report/github.com/GoogleCloudPlatform/spark-on-k8s-operator)

**This work is in progress and experimental**

This repository is an attempt to run cloud-native, on-demand and self-healing Spark on Kubernetes natively on Openstack private cloud.
It is an alternative approach to [cern-spark-service](https://pypi.org/project/cern-spark-service/)

Repository is based on [GoogleCloudPlatform/spark-on-k8s-operator](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator)

## Architecture

* [SparkOperator and sparkctl Design](docs/design.md)
* [Original project](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator)

## User guide - cluster management and submitting applications

* [Openstack Spark cluster management - opsparkctl](cmd/README.md)
* [Application examples](examples)
* [Submit Spark jobs - sparkctl](sparkctl/README.md)

## Spark Operator overview

* [Quick Start Guide - SparkOperator](docs/quick-start-guide.md)
* [API Specification - SparkOperator](docs/api.md) 
* [Detailed Guide - SparkOperator ](docs/user-guide.md)

## Motivations

This approach is to have the submission client create a CRD object. Having externally 
created and managed CRD objects offer the following benefits:
* Things like creating namespaces and setting up RBAC roles and resource quotas represent a separate concern and are better 
done before applications get submitted.
* With the external CRD controller submitting applications on behalf of users, they don't need to deal with the submission 
process and the `spark-submit` command. Instead, the focus is shifted from thinking about commands to thinking about declarative 
YAML files describing Spark applications that can be easily version controlled. 
* Externally created CRD objects make it easier to integrate Spark application submission and monitoring with users' existing 
pipelines and tooling on Kubernetes.
* Internally created CRD objects are good for capturing and communicating application/executor status to the users, but not 
for driver/executor pod configuration/customization as very likely it needs external input. Such external input most likely 
need additional command-line options to get passed in.

Additionally, keeping the CRD implementation outside the Spark repository gives us a lot of flexibility in terms of 
functionality to add to the CRD controller. We also have full control over code review and release process.
