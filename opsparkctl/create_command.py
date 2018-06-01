from . import base_command

class KubeOpenstackCreateCommand(base_command.BaseCommand):
    def run(self, args, additional):
        from . import openstack_client
        from . import kube_config

        # Initialize client
        client = openstack_client.CernOpentackClient()
        kube_config_client = kube_config.KubeConfigClient()

        # Select a project in openstack
        selected_project = client.get_project()

        # Create kube cluster
        name = client.create_cluster(selected_project.id)

        # Get created cluster config
        kube_cluster_info = client.get_cluster(selected_project.id, name)

        # Save cluster info
        kube_config_client.save_cluster_info(kube_cluster_info)

        # Test cluster info
        kube_config_client.load_local_config()

        return True


class KubeOpenstackFetchCommand(base_command.BaseCommand):
    def run(self, args, additional):
        from . import openstack_client
        from . import kube_config

        # Initialize client
        client = openstack_client.CernOpentackClient()
        kube_config_client = kube_config.KubeConfigClient()

        # Select a project in openstack
        selected_project = client.get_project()

        # Select kube cluster
        name = client.select_cluster(selected_project.id)

        # Get created cluster config
        kube_cluster_info = client.get_cluster(selected_project.id, name)

        # Save cluster info
        kube_config_client.save_cluster_info(kube_cluster_info)

        # Test cluster info
        kube_config_client.load_local_config()

        return True


class KubeSparkCreateCommand(base_command.BaseCommand):
    def run(self, args, additional):
        from . import kube_config
        from . import spark_kube_client

        kube_config_client = kube_config.KubeConfigClient()

        c = kube_config_client.load_local_config()
        spark_client = spark_kube_client.SparkK8SApi(c)

        spark_client.create_spark_operator_base()
        return True



