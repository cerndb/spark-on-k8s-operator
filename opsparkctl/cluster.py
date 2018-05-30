from kubernetes import client


class KubeClusterInfo(object):
    def __init__(self, name, api_address, ca, key, cert):
        self.name = name
        self.api_address = api_address
        self.ca = ca # Full content of certificate
        self.key = key # Full content of certificate
        self.cert = cert # Full content of certificate

    def __repr__(self):
        return "<Name: %s>, <IP: %s>, <CA: %s>, <KEY: %s>, <CERT: %s>" % (self.name, self.api_address, self.ca, self.key, self.cert)


class SparkKubeBase():

    def __init__(self, c):
        self.configuration = c
        self.k8s_client = client.ApiClient(configuration=self.configuration)


class SparkKubeApi(SparkKubeBase):
    pass

