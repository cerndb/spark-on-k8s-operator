from . import base_command


class KubeSparkUpdateCommand(base_command.BaseCommand):
    def run(self, args, additional):
        from . import kube_config
        from . import spark_kube_client

        kube_config_client = kube_config.KubeConfigClient()

        c = kube_config_client.load_local_config()
        spark_client = spark_kube_client.SparkK8SApi(c)

        spark_client.update_spark_operator_base()
        return True


class KubeSparkHistoryUpdateCommand(base_command.BaseCommand):
    def run(self, args, additional):
        from . import kube_config
        from . import spark_kube_client

        kube_config_client = kube_config.KubeConfigClient()

        c = kube_config_client.load_local_config()
        spark_client = spark_kube_client.SparkK8SApi(c)

        spark_client.update_spark_history()
        return True
