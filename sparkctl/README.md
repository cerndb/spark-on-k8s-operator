# sparkctl

`sparkctl` is a command-line tool of the Spark Operator for creating, listing, checking status of, getting logs of, 
and deleting `SparkApplication`s. It can also do port forwarding from a local port to the Spark web UI port for 
accessing the Spark web UI on the driver. Each function is implemented as a sub-command of `sparkctl`.

To build `sparkctl`, make sure you followed build steps [here](https://github.com/GoogleCloudPlatform/spark-on-k8s-operator/blob/master/docs/quick-start-guide.md#build) and have all the dependencies, then run the following command from within `sparkctl/`:

```bash
$ go build -o sparkctl
```

## Flags

The following global flags are available for all the sub commands:
* `--namespace`: the Kubernetes namespace of the `SparkApplication`(s). Defaults to `default`.
* `--kubeconfig`: the path to the file storing configuration for accessing the Kubernetes API server. Defaults to 
`$HOME/.kube/config`

## Available Commands

### Create

`create` is a sub command of `sparkctl` for parsing and creating a `SparkApplication` object in namespace specified by 
`--namespace` the from a given YAML file. It parses the YAML file, and sends the parsed `SparkApplication` object 
parsed to the Kubernetes API server.

Usage:
```bash
$ sparkctl create <path to YAML file>
```

The `create` command also supports shipping local Hadoop configuration files into the driver and executor pods. 
Specifically, it detects local Hadoop configuration files located at the path specified by the 
environment variable `HADOOP_CONF_DIR`, create a Kubernetes `ConfigMap` from the files, and adds the `ConfigMap` to
the `SparkApplication` object so it gets mounted into the driver and executor pods by the Spark Operator. The 
environment variable `HADOOP_CONF_DIR` is also set in the driver and executor containers.    

#### Staging local dependencies

The `create` command also supports staging local application dependencies, though currently only uploading to a Google 
Cloud Storage (GCS) bucket is supported. The way it works is as follows. It checks if there is any local dependencies 
in `spec.mainApplicationFile`, `spec.deps.jars`, `spec.deps.files`, etc. in the parsed `SaprkApplication` object. If so, 
it tries to upload the local dependencies to the remote location specified by `--upload-to`. The command fails if local
dependencies are used but `--upload-to` is not specified. By default, a local file that already exists remotely, i.e., 
there exists a file with the same name and upload path remotely, will be ignored. If the remote file should be overridden
instead, the `--override` flag should be specified.

##### Uploading to GCS

For uploading to GCS, the value should be in the form of `gs://<bucket>`. The bucket must exist and uploading fails if 
otherwise. The local dependencies will be uploaded to the path 
`spark-app-dependencies/<SparkApplication namespace>/<SparkApplication name>` in the given bucket. It replaces the 
file path of each local dependency with the URI of the remote copy in the parsed `SparkApplication` object if uploading
is successful. 

Usage:
```bash
$ sparkctl create <path to YAML file> --upload-to gs://<bucket> --project <GCP project the GCS bucket is associated to>
```

Note that uploading to GCS requires a GCP service account with the necessary IAM permission to use the GCP project 
specified by `--project` (`serviceusage.services.use`) and the permission to create GCS objects (`storage.object.create`). 
The service account JSON key file must be locally available and be pointed to by the environment variable 
`GOOGLE_APPLICATION_CREDENTIALS`. For more information on IAM authentication, please check 
[Getting Started with Authentication](https://cloud.google.com/docs/authentication/getting-started).

By default, the uploaded dependencies are not made publicly accessible and are referenced using URIs in the form of 
`gs://bucket/path/to/file`. Such dependencies are referenced through URIs of the form `gs://bucket/path/to/file`. To 
download the dependencies from GCS, a custom-built Spark init-container with the 
[GCS connector](https://cloud.google.com/dataproc/docs/concepts/connectors/cloud-storage) installed and necessary
Hadoop configuration properties specified is needed. An example Docker file of such an init-container can be found 
[here](https://gist.github.com/liyinan926/f9e81f7b54d94c05171a663345eb58bf). 

If you want to make uploaded dependencies publicly available so they can be downloaded by the built-in init-container,
simply add `--public` to the `create` command, as the following example shows:

```bash
$ sparkctl create <path to YAML file> --upload-to gs://<bucket> --project <GCP project the GCS bucket is associated to> --public
``` 

Publicly available files are referenced through URIs of the form `https://storage.googleapis.com/bucket/path/to/file`.

##### Uploading to S3 (S3A)

For uploading to S3, the value should be in the form of `s3a://<bucket>`. The bucket must exist and uploading fails if 
otherwise. The local dependencies will be uploaded to the path 
`spark-app-dependencies/<SparkApplication namespace>/<SparkApplication name>` in the given bucket. It replaces the 
file path of each local dependency with the URI of the remote copy in the parsed `SparkApplication` object if uploading
is successful. 

Usage:
```bash
$ sparkctl create <path to YAML file> --upload-to s3a://<bucket>
```

Note that uploading to S3 with [AWS SDK](https://docs.aws.amazon.com/sdk-for-go/v1/developer-guide/configuring-sdk.html) requires credentials to be specified. 
For GCP, the S3 Interoperability credentials can be retrieved as described [here](https://cloud.google.com/storage/docs/migrating#keys). 
SDK uses the default credential provider chain to find AWS credentials. The SDK uses the first provider in the chain that returns credentials without an error. 
The default provider chain looks for credentials in the following order:

- Environment variables
    ```
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
    AWS_SESSION_TOKEN (optional)
    ```
- Shared credentials file (.aws/credentials)
    ```
    [default]
    aws_access_key_id = <YOUR_ACCESS_KEY_ID>
    aws_secret_access_key = <YOUR_SECRET_ACCESS_KEY>
    ```
- If your application is running on an Amazon EC2 instance, IAM role for Amazon EC2.

For more information about AWS SDK authentication, please check 
[Specifying Credentials](https://docs.aws.amazon.com/sdk-for-go/v1/developer-guide/configuring-sdk.html#specifying-credentials).

By default, the uploaded dependencies are not made publicly accessible and are referenced using URIs in the form of 
`s3a://bucket/path/to/file`. Such dependencies are referenced through URIs of the form `s3a://bucket/path/to/file`. To 
download the dependencies from S3, a custom-built Spark init-container with the required 
jars ( e.g. `hadoop-aws-2.7.6.jar`, `aws-java-sdk-1.7.6.jar`) in your classpath, 
and `spark-default.conf` with the AWS keys and the S3A FileSystemClass (you can also use `hadoopConf` in the SparkApplication YAML):

```
spark.hadoop.fs.s3a.access.key XXXXXXX
spark.hadoop.fs.s3a.secret.key XXXXXXX
spark.hadoop.fs.s3a.impl org.apache.hadoop.fs.s3a.S3AFileSystem
```

NOTE: In Spark 2.3.0 with init-containers used for Spark with Kubernetes as resource manager, 
the dependencies are not mounted in proper location (e.g. application file is not mounted in jars folder)

If you want to make uploaded dependencies publicly available so they can be downloaded by the built-in init-container,
simply add `--public` to the `create` command, as the following example shows:

```bash
$ sparkctl create <path to YAML file> --upload-to s3a://<bucket> --public
``` 

Publicly available files are referenced through URIs of the form `https://<bucket>.storage.googleapis.com/path/to/file`.

If you want to use custom S3 endpoint, add `--endpoint-url` and `--region`:

```bash
$ sparkctl create <path to YAML file> --endpoint-url <endpoint-protocol>://<endpoint-url> --region <endpoint-region> --upload-to s3://<bucket>
``` 

In that case, publicly available files are referenced through URIs of the form `<endpoint-protocol>://<bucket>.<endpoint-url>/path/to/file`.

### List

`list` is a sub command of `sparkctl` for listing `SparkApplication` objects in the namespace specified by 
`--namespace`.

Usage:
```bash
$ sparkctl list
```

### Status

`status` is a sub command of `sparkctl` for checking and printing the status of a `SparkApplication` in the namespace 
specified by `--namespace`.

Usage:
```bash
$ sparkctl status <SparkApplication name>
```

### Log

`log` is a sub command of `sparkctl` for fetching the logs of a pod of `SparkApplication` with the given name in the 
namespace specified by `--namespace`. The command by default fetches the logs of the driver pod. To make it fetch logs
of an executor pod instead, use the flag `--executor` or `-e` to specify the ID of the executor whose logs should be 
fetched.

The `log` command also supports streaming the driver or executor logs with the `--follow` or `-f` flag. It works in the 
same way as `kubectl logs -f`, i.e., it streams logs until no more logs are available.

Usage:
```bash
$ sparkctl log <SparkApplication name> [-e <executor ID, e.g., 1>] [-f]
```

### Delete

`status` is a sub command of `sparkctl` for delete `SparkApplication` with the given name in the namespace 
specified by `--namespace`.

Usage:
```bash
$ sparkctl delete <SparkApplication name>
```

### Forward

`forward` is a sub command of `sparkctl` for doing port forwarding from a local port to the Spark web UI port on the 
driver. It allows the Spark web UI served in the driver pod to be accessed locally. By default, it forwards from local
port `4040` to remote port `4040`, which is the default Spark web UI port. Users can specify different local port
and remote port using the flags `--local-port` and `--remote-port`, respectively. 

Usage:
```bash
$ sparkctl forward <SparkApplication name> [--local-port <local port>] [--remote-port <remote port>]
```

Once port forwarding starts, users can open `127.0.0.1:<local port>` or `localhost:<local port>` in a browser to access
the Spark web UI. Forwarding continues until it is interrupted or the driver pod terminates.
