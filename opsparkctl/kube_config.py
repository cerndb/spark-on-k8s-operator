from kubernetes import config
from kubernetes.client import Configuration
import os
import errno


class KubeClusterInfo(object):
    def __init__(self, name, api_address, ca, key, cert):
        self.name = name
        self.api_address = api_address
        self.ca = ca # Full content of certificate
        self.key = key # Full content of certificate
        self.cert = cert # Full content of certificate

    def __repr__(self):
        return "<Name: %s>, <IP: %s>, <CA: %s>, <KEY: %s>, <CERT: %s>" % (self.name, self.api_address, self.ca, self.key, self.cert)


class KubeConfigClient(object):
    def __init__(self):
        self._cfg_dir_base = os.path.join(os.path.expanduser("~"), '.kube')
        self._prepare_cfg_dir(self._cfg_dir_base)

    def _prepare_cfg_dir(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

    def save_cluster_info(self, kube_cluster_info):
        self._cfg_file = os.path.join(self._cfg_dir_base, 'config')

        for k in ('key', 'cert', 'ca'):
            attribute = getattr(kube_cluster_info, "%s" % k)

            fname = "%s/%s.pem" % (self._cfg_dir_base, k)
            f = open(fname, "w")
            f.write(attribute)
            f.close()

        cfg = ("apiVersion: v1\n"
               "clusters:\n"
               "- cluster:\n"
               "    certificate-authority: %(cfg_dir)s/ca.pem\n"
               "    server: %(api_address)s\n"
               "  name: %(name)s\n"
               "contexts:\n"
               "- context:\n"
               "    cluster: %(name)s\n"
               "    user: admin\n"
               "  name: default\n"
               "current-context: default\n"
               "kind: Config\n"
               "preferences: {}\n"
               "users:\n"
               "- name: admin\n"
               "  user:\n"
               "    client-certificate: %(cfg_dir)s/cert.pem\n"
               "    client-key: %(cfg_dir)s/key.pem\n"
               % {'name': kube_cluster_info.name,
                  'api_address': kube_cluster_info.api_address,
                  'cfg_dir': self._cfg_dir_base})

        f = open(self._cfg_file, "w")
        f.write(cfg)
        f.close()

    def load_local_config(self):
        print
        print "[Kubernetes client configuration..]"
        self._cfg_file = os.path.join(self._cfg_dir_base, 'config')

        if not os.path.exists(self._cfg_file):
            raise Exception("Cannot find configuration for cluster at %s"%(self._cfg_file))

        # Load default configuration
        config.load_kube_config(config_file=self._cfg_file)
        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)

        # Extend with cluster name
        with open(self._cfg_file, 'r') as f:
            import yaml
            config_file = yaml.load(f)
            name = config_file["clusters"][0]["name"]
            c.name = name

            print("Kubernetes config used: %s" % self._cfg_file)
            print("Kubernetes cluster name: %s" % c.name)
            print("Kubernetes master: %s" % c.host)
            return c
