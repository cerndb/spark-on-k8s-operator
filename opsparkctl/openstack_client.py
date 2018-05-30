from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneauth1.extras import kerberos
from keystoneclient.v3.client import Client as KeystoneClient
from magnumclient.client import Client as MagnumClient
from magnumclient.common import utils as magnum_utils
from novaclient.client import Client as NovaClient
from . import cluster

import qprompt
import base64
import getpass
import math
import sys
import time


class CernOpentackClient(object):
    # TODO: generalize to use OpenstackClient instead of CernOpentackClient using some opsparkctl.conf file
    # TODO: so other people can build their own packages and customize
    __OS_AUTH_KRB_URL = "https://keystone.cern.ch/krb/v3"
    __OS_AUTH_PASS_URL = "https://keystone.cern.ch/main/v3"
    __OS_PROJECT_DOMAIN_ID = "default"
    __OS_USER_DOMAIN_NAME="Default"
    __OS_USERNAME=None
    __OS_PASSWORD=None
    __KUBE_TEMPLATE = "kubernetes-alpha"
    __OS_REGION_NAME = "cern"
    __OS_INTERFACE = "public"
    __OS_IDENTITY_API_VERSION = 3
    __MAGNUM_CLIENT_VERSION = '1'
    __NOVA_CLIENT_VERSION = '2'
    __OS_PROJECT_ID = ""
    __OS_PROJECT_NAME = ""
    __KUBE_CLUSTER_LABELS = {
            "cvmfs_tag" : "qa",
            "flannel_backend" : "vxlan",
            "influx_grafana_dashboard_enabled" : "true",
            "ingress_controller" : "traefik",
            "kube_tag" : "v1.10.1",
            "container_infra_prefix" : "gitlab-registry.cern.ch/cloud/atomic-system-containers/",
            "kubeapi_options" : "--admission-control=Initializers --runtime-config=admissionregistration.k8s.io/v1alpha1",
        }

    def init_session(self, project_id = ""):
        if self.__OS_PASSWORD is None or self.__OS_USERNAME is None:
            krb5 = kerberos.KerberosMethod(mutual_auth="disabled")
            auth = v3.Auth(auth_url=self.__OS_AUTH_KRB_URL,
                           auth_methods = [krb5],
                           project_id = project_id,
                           project_domain_id=self.__OS_PROJECT_DOMAIN_ID)
            krb_session =  session.Session(auth=auth)

            try:
                krb_session.get_auth_headers()
                return krb_session
            except Exception as e:
                print e.message

            print "Kerberos authentication failed!! Probably [kinit <your-user-name>] missing. " \
                  "Abort or continue with PasswordMethod. Trying password authentication.."

        password = v3.PasswordMethod(username=self.__get_username(),
                                     password=self.__get_password(),
                                     user_domain_name=self.__OS_USER_DOMAIN_NAME)
        auth = v3.Auth(auth_url=self.__OS_AUTH_PASS_URL,
                auth_methods=[password],
                project_id = project_id,
                project_domain_id=self.__OS_PROJECT_DOMAIN_ID)
        pass_session = session.Session(auth=auth)

        try:
            pass_session.get_auth_headers()
            return pass_session
        except Exception as e:
            print e.message

        raise Exception("Could not authenticate")

    def __get_username(self):
        if not self.__OS_USERNAME:
            self.__OS_USERNAME = raw_input("Username: ")
        return self.__OS_USERNAME

    def __get_password(self):
        if not self.__OS_PASSWORD:
            try:
                password = getpass.getpass()
                self.__OS_PASSWORD = base64.b64encode(password)
            except Exception as error:
                print('ERROR', error)
        return base64.b64decode(self.__OS_PASSWORD)

    def get_project(self):
        keystone = KeystoneClient(session=self.init_session(""))

        # Select project
        projects = keystone.auth.projects()
        menu = qprompt.Menu()
        for i in range(0, len(projects)):
            project = projects[i]
            menu.add(str(i), project.name)
        print
        choice = menu.show(header="Select Openstack project in which to configure cluster")
        selected_project = projects[int(choice)]
        return selected_project

    def create_cluster(self, project_id):
        session = self.init_session(project_id)
        magnum = MagnumClient('1', session=session)
        nova = NovaClient('2', session=session)

        # Select name
        name = self.__get_cluster_name()

        # Number of masters
        masters_number = 1

        # Number of nodes
        nodes_number = self.__get_number_nodes(magnum, nova)

        # Select keypair
        keypair = self.__get_keypair(nova)

        # Create cluster
        magnum.clusters.create(keypair=keypair.name,
                               cluster_template_id=self.__KUBE_TEMPLATE,
                               name=name,
                               node_count=nodes_number,
                               master_count=masters_number,
                               labels=self.__KUBE_CLUSTER_LABELS).to_dict()

        print
        sys.stdout.write("Kubernetes cluster [name: %s] creation in progress.."%(name))
        while 1:
            cluster_config = magnum.clusters.get(name)
            if cluster_config.status in ('CREATE_FAILED', 'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'ROLLBACK_COMPLETE', 'CREATE_CLUSTER_FAIL'):
                print cluster_config.status
                break

            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(5)

        return name

    def select_cluster(self, project_id):
        session = self.init_session(project_id)
        magnum = MagnumClient('1', session=session)
        clusters = magnum.clusters.list()
        menu = qprompt.Menu()
        for i in range(0, len(clusters)):
            cluster = clusters[i]
            if cluster.status in ('CREATE_COMPLETE', 'UPDATE_COMPLETE', 'ROLLBACK_COMPLETE'):
                menu.add(str(i), cluster.name)
        print
        choice = menu.show(header="Select cluster to configure")
        selected_cluster = clusters[int(choice)]
        return selected_cluster.name

    def get_pems(self, project_id, opts):
        session = self.init_session(project_id)
        magnum = MagnumClient('1', session=session)

        tls = magnum_utils.generate_csr_and_key()
        tls['ca'] = magnum.certificates.get(**opts).pem
        opts['csr'] = tls['csr']
        tls['cert'] = magnum.certificates.create(**opts).pem
        return tls

    def get_cluster_info(self, project_id, cluster_name):
        session = self.init_session(project_id)
        magnum = MagnumClient('1', session=session)
        return magnum.clusters.get(cluster_name)

    def get_cluster(self, project_id, cluster_name):
        print
        print "Kubernetes cluster [name: %s] configuration init" % (cluster_name)

        cluster_config = self.get_cluster_info(project_id, cluster_name)
        opts = {
            'cluster_uuid': cluster_config.uuid,
        }

        tls = self.get_pems(project_id, opts)
        return cluster.KubeClusterInfo(cluster_config.name, cluster_config.api_address, tls['ca'], tls['key'], tls['cert'])

    def __get_cluster_name(self):
        print
        return qprompt.ask_str(msg="What should be the cluster name?")

    def __get_number_nodes(self, magnum, nova):
        kub_template = magnum.cluster_templates.get(self.__KUBE_TEMPLATE)
        selected_flavor = None
        for flavor in nova.flavors.list():
            if flavor.name == kub_template.flavor_id:
                selected_flavor = flavor
                break

        if selected_flavor is None:
            raise Exception("Could not find available flavour in your project for the template - " + self.__KUBE_TEMPLATE)

        print
        print str(selected_flavor)
        node_vcpus =  selected_flavor.vcpus
        node_ram = selected_flavor.ram

        limits = nova.limits.get().absolute
        limits_dict = dict(map(lambda x: (x.name, x.value), list(limits)))
        cores_available = limits_dict['maxTotalCores'] - limits_dict['totalCoresUsed']
        ram_available = limits_dict['maxTotalRAMSize'] - limits_dict['totalRAMUsed']

        cores_max_nodes = int(math.floor(cores_available / node_vcpus))
        ram_max_nodes = int(math.floor(ram_available / node_ram))

        if (cores_max_nodes > ram_max_nodes):
            max_nodes = ram_max_nodes
        else:
            max_nodes = cores_max_nodes

        max_nodes = max_nodes - 1 # reserve one for kubernetes master
        if max_nodes < 1:
            raise Exception("Could not create the cluster in this project for the template - " + self.__KUBE_TEMPLATE)
        return qprompt.ask_int(msg="Now many nodes in the cluster you want to create? MAX:"+str(max_nodes), vld=range(1, max_nodes+1))

    def __get_keypair(self, nova):
        keypairs = nova.keypairs.list()
        menu = qprompt.Menu()
        for i in range(0, len(keypairs)):
            keypair = keypairs[i]
            menu.add(str(i), keypair.name)
        print
        choice = menu.show(header="Select Openstack keypair to create cluster")
        selected_keypair = keypairs[int(choice)]
        return selected_keypair

    def __set_project(self, id, name):
        self.__OS_PROJECT_ID = id
        self.__OS_PROJECT_NAME = name

    def __get_project_id(self):
        return self.__OS_PROJECT_ID

    def __get_project_name(self):
        return self.__OS_PROJECT_NAME
