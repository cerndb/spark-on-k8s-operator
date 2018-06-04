"""Command-line interface to the Spark on Kubernetes over Openstack cluster management tool"""

import argparse
import sys
from . import __version__
from . import create_command
from . import update_command
from . import status_command

min_version = __version__.__python_min_version__.split('.')
if not (sys.version_info[0] >= int(min_version[0]) and sys.version_info[1] >= int(min_version[1]) and sys.version_info[2] >= int(min_version[2])):
    print "Your python version(%s) is lower than required (%s)" % (
    str(sys.version_info[:3]), __version__.__python_min_version__)
    print "Please refer to documentation for help"
    print "%s" % (__version__.__url__)
    exit(2)


class SparkServiceArgumentParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs):
        super(SparkServiceArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        """error(message: string)
        Prints a usage message incorporating the message to stderr and
        exits.
        """
        self.print_usage(sys.stderr)
        choose_from = ' (choose from'
        progparts = self.prog.partition(' ')
        self.exit(2, "error: %(errmsg)s\nTry '%(mainp)s --help %(subp)s'"
                     " for more information.\n" %
                     {'errmsg': message.split(choose_from)[0],
                      'mainp': progparts[0],
                      'subp': progparts[2]})


class SparkServiceShell(object):
    def run(self, argv):
        parser = SparkServiceArgumentParser(
            prog='opsparkctl',
            description=__doc__.strip(),
            epilog='See "opsparkctl --help COMMAND" '
                   'for help on a specific command.',
            add_help=True,
        )

        parser.add_argument('-v', '--version', action='version', version="%(prog)s (" + __version__.__version__ + ")")

        subparsers = parser.add_subparsers(help='commands', dest='command')

        # Create command
        create_parser = subparsers.add_parser(
            'create', help='Create, configure and initialize spark on kubernetes cluster')
        create_subparser = create_parser.add_subparsers(help='create commands', dest='create_command')
        ## Create kube command
        create_subparser.add_parser(
            'kube', help='Create a kubernetes cluster over Openstack and fetch configuration locally')
        ## Create local config command
        create_subparser.add_parser(
            'local-kube-config', help='Fetch locally kubernetes cluster configuration')
        ## Create spark command
        create_subparser.add_parser(
            'spark', help='Creates Spark on Kubernetes Operator on the cluster')
        ## Create spark-history command
        create_subparser.add_parser(
            'spark-history', help='Creates Spark on Kubernetes Operator on the cluster')

        # Update command
        update_parser = subparsers.add_parser(
            'update', help='Update components of spark on kubernetes cluster')
        update_subparser = update_parser.add_subparsers(help='update commands', dest='update_command')
        ## Update spark command
        update_subparser.add_parser(
            'spark', help='Update Spark on Kubernetes Operator on the cluster')
        ## Update spark-history command
        update_subparser.add_parser(
            'spark-history', help='Creates Spark on Kubernetes Operator on the cluster')

        # Update command
        status_parser = subparsers.add_parser(
            'status', help='Get status of spark on kubernetes cluster')

        # Parse and route to proper class
        args, additional = parser.parse_known_args()

        if args.command == 'create':
            if args.create_command == 'kube' and not create_command.KubeOpenstackCreateCommand().run(args, additional):
                print "** ERROR **"
                print "Check command, for help: opsparkctl create kube --help"
            elif args.create_command == 'local-kube-config' and not create_command.KubeOpenstackFetchCommand().run(args, additional):
                print "** ERROR **"
                print "Check command, for help: opsparkctl create local-kube-config --help"
            elif args.create_command == 'spark' and not create_command.KubeSparkCreateCommand().run(args, additional):
                print "** ERROR **"
                print "Check command, for help: opsparkctl create spark --help"
            elif args.create_command == 'spark-history' and not create_command.KubeSparkHistoryCreateCommand().run(args, additional):
                print "** ERROR **"
                print "Check command, for help: opsparkctl create spark-history --help"
        elif args.command == 'update':
            if args.update_command == 'spark' and not update_command.KubeSparkUpdateCommand().run(args, additional):
                print "** ERROR **"
                print "Check command, for help: opsparkctl update spark --help"
            elif args.update_command == 'spark-history' and not update_command.KubeSparkHistoryUpdateCommand().run(args, additional):
                print "** ERROR **"
                print "Check command, for help: opsparkctl update spark-history --help"
        elif args.command == 'status':
            if not status_command.KubeSparkStatusCommand().run(args, additional):
                print "** ERROR **"
                print "Check command, for help: opsparkctl status --help"


def main(argv=None):
    return SparkServiceShell().run(argv)


if __name__ == "__main__":
    sys.exit(main())