
class BaseCommand(object):
    def run(self, args, additional):
        """
        :param args array: arguments passed to the command
        :param additional array: additional arguments passed to the command
        :return: bool: whether command was successful or not
        """
        raise Exception('This Command is not supported')