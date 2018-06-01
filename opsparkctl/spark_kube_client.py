from kubernetes import client
import qprompt
from kubernetes.client.rest import ApiException
import yaml
import pkgutil
import boto.s3.connection
import datetime
class SparkK8SBase():

    def __init__(self, c):
        self.configuration = c
        self.k8s_client = client.ApiClient(configuration=self.configuration)

class SparkK8SApi(SparkK8SBase):

    @staticmethod
    def __get_s3_metadata():
        endpoint = qprompt.ask_str(msg="S3 Endpoint", dft="cs3.cern.ch")
        access_key = qprompt.ask_str(msg="S3 Access Key", dft="")
        secret_key = qprompt.ask_str(msg="S3 Secret", dft="")
        is_secure = False

        return access_key, secret_key, endpoint, is_secure

    @staticmethod
    def __get_s3_connection(endpoint, access_key, secret_key, is_secure=True):
        return boto.s3.connection.S3Connection(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            host=endpoint,
            is_secure=is_secure,
            calling_format=boto.s3.connection.SubdomainCallingFormat(),
        )

    def __get_object_metadata(self, object_loaded):
        api_version = object_loaded["apiVersion"]
        kind = object_loaded["kind"]
        name = None
        namespace = None
        if 'metadata' in object_loaded:
            if 'namespace' in object_loaded["metadata"]:
                namespace = object_loaded["metadata"]["namespace"]
            if 'name' in object_loaded["metadata"]:
                name = object_loaded["metadata"]["name"]
        return api_version, kind, name, namespace

    def __get_api_instance(self, api_version):
        if api_version == "v1":
            return client.CoreV1Api(self.k8s_client)
        elif api_version == "apps/v1beta1":
            return client.AppsV1beta1Api(self.k8s_client)
        elif api_version == "rbac.authorization.k8s.io/v1beta1":
            return client.RbacAuthorizationV1beta1Api(self.k8s_client)
        else:
            raise Exception("Unsupported api type [%s]" % api_version)

    def __check_resource(self, object_loaded):
        api_version, kind, name, namespace = self.__get_object_metadata(object_loaded)

        try:
            api_instance = self.__get_api_instance(api_version)
            if kind == "ConfigMap":
                return api_instance.read_namespaced_config_map(name=name, namespace=namespace)
            elif kind == "Deployment":
                return api_instance.read_namespaced_deployment(name=name, namespace=namespace)
            elif kind == "ServiceAccount":
                return api_instance.read_namespaced_service_account(name=name, namespace=namespace)
            elif kind == "Namespace":
                return api_instance.read_namespace(name=name)
            elif kind == "Role":
                return api_instance.read_namespaced_role(name=name, namespace=namespace)
            elif kind == "ClusterRole":
                return api_instance.read_cluster_role(name=name)
            elif kind == "ClusterRoleBinding":
                return api_instance.read_cluster_role_binding(name=name)
            elif kind == "RoleBinding":
                return api_instance.read_namespaced_role_binding(name=name, namespace=namespace)
            else:
                raise Exception("Unsupported object kind [%s] for resource check" % kind)
        except ApiException:
            return False

    def __create_resource(self, object_loaded, ignore_exists=False):
        if ignore_exists and self.__check_resource(object_loaded):
            api_version, kind, name, namespace = self.__get_object_metadata(object_loaded)
            print("WARNING: create skipped [%s]/[%s %s]: Exists" % (name, kind, namespace))
            return

        api_version, kind, name, namespace = self.__get_object_metadata(object_loaded)
        try:
            api_instance = self.__get_api_instance(api_version)

            if kind == "ConfigMap":
                api_instance.create_namespaced_config_map(namespace=namespace, body=object_loaded)
            elif kind == "Deployment":
                api_instance.create_namespaced_deployment(namespace=namespace, body=object_loaded)
            elif kind == "ServiceAccount":
                api_instance.create_namespaced_service_account(namespace=namespace, body=object_loaded)
            elif kind == "Namespace":
                api_instance.create_namespace(body=object_loaded)
            elif kind == "Role":
                api_instance.create_namespaced_role(namespace=namespace, body=object_loaded)
            elif kind == "ClusterRole":
                api_instance.create_cluster_role(body=object_loaded)
            elif kind == "ClusterRoleBinding":
                api_instance.create_cluster_role_binding(body=object_loaded)
            elif kind == "RoleBinding":
                api_instance.create_namespaced_role_binding(namespace=namespace, body=object_loaded)
            else:
                raise Exception("Unsupported object kind [%s] for resource creation" % kind)
        except ApiException as e:
            print("ERROR: create unsuccessful [%s]/[%s %s]: %s" % (name, kind, namespace, e.reason))
            exit(2)
        except ValueError as e:
            if 'pending' in e.message:
                #TODO: Handle case of Initializers bug, remove me in the future
                print("INFO: Spark Operator Initializer pending status not reported")
            else:
                raise ValueError(e.message)

        print("SUCCESS: create object [%s]/[%s %s]" % (name, kind, namespace))
        return True

    def __replace_resource(self, object_loaded):
        api_version, kind, name, namespace = self.__get_object_metadata(object_loaded)
        try:
            api_instance = self.__get_api_instance(api_version)

            if kind == "ConfigMap":
                api_instance.replace_namespaced_config_map(name=name, namespace=namespace, body=object_loaded)
            elif kind == "Deployment":
                # Update deployment template label
                object_loaded["spec"]["template"]["metadata"]["labels"]["date"] = datetime.datetime.now().strftime("%s")
                api_instance.replace_namespaced_deployment(name=name, namespace=namespace, body=object_loaded)
            else:
                raise Exception("Unsupported object kind [%s] for resource creation" % kind)
        except ApiException as e:
            print("WARNING: create unsuccessful [%s]/[%s %s]: %s" % (name, kind, namespace, e.reason))
            return False
        except ValueError as e:
            if 'pending' in e.message:
                #TODO: Handle case of Initializers bug, remove me in the future
                print("INFO: Spark Operator Initializer pending status not reported")
            else:
                raise ValueError(e.message)

        print("SUCCESS: update object [%s]/[%s %s]" % (name, kind, namespace))
        return True

    def __create_yaml_resources(self, body, ignore_exists=False, update=False):
        # create an instance of the API class
        objects_loaded = yaml.load_all(body)
        for object_loaded in objects_loaded:
            if update:
                if not self.__replace_resource(object_loaded):
                    ## Try to create if replace fails
                    self.__create_resource(object_loaded, ignore_exists)
            else:
                self.__create_resource(object_loaded, ignore_exists)

    def _create_spark_rbac(self):
        # Create spark rbac if does not exists
        spark_rbac_data = pkgutil.get_data('manifest', "spark-operator-base/spark-rbac.yaml")
        return self.__create_yaml_resources(spark_rbac_data, ignore_exists=True)

    def _create_spark_operator_rbac(self):
        # Create spark rbac if does not exists
        spark_rbac_data = pkgutil.get_data('manifest', "spark-operator-base/spark-operator-rbac.yaml")
        return self.__create_yaml_resources(spark_rbac_data, ignore_exists=True)

    def _create_spark_operator_data(self, update=False):
        access_key, secret_key, endpoint, is_secure = SparkK8SApi.__get_s3_metadata()
        cluster_name = self.configuration.name

        # Ensure bucket exists
        print("INFO: ensure bucket s3://%s in s3 exists" % cluster_name)
        s3_connection = SparkK8SApi.__get_s3_connection(endpoint, access_key, secret_key, is_secure)
        bucket = s3_connection.lookup(cluster_name)
        if not bucket:
            s3_connection.create_bucket(cluster_name)
        print("INFO: ensure bucket in s3 has s3://%s/spark-events initialized" % cluster_name)
        spark_events_key = "spark-events/init"
        key = bucket.get_key(spark_events_key)
        if not key:
            key = bucket.new_key(spark_events_key)
        key.set_contents_from_string('Spark Events initialized')

        spark_defaults_conf_data = pkgutil.get_data('manifest', "spark-operator/spark-config.yaml").format(
            endpoint=endpoint,
            access=access_key,
            secret=secret_key,
            cluster=cluster_name)
        return self.__create_yaml_resources(spark_defaults_conf_data, ignore_exists=False, update=update)

    def _create_spark_operator_deployment(self, update=False):
        spark_operator = pkgutil.get_data('manifest', "spark-operator/spark-operator.yaml")
        return self.__create_yaml_resources(spark_operator, ignore_exists=False, update=update)

    def create_spark_operator_base(self):
        print
        print "[Spark on kubernetes rbac init..]"
        self._create_spark_rbac()

        print
        print "[Spark on kubernetes operator rbac init..]"
        self._create_spark_operator_rbac()

        print
        print "[Spark on kubernetes operator config data init..]"
        self._create_spark_operator_data(update=False)

        print
        print "[Spark on kubernetes operator init..]"
        self._create_spark_operator_deployment(update=False)

    def update_spark_operator_base(self):
        print
        print "[Spark on kubernetes operator config data update..]"
        self._create_spark_operator_data(update=True)

        print
        print "[Spark on kubernetes operator update..]"
        self._create_spark_operator_deployment(update=True)




