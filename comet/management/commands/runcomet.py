from django.utils import autoreload
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import re

address_port_re = re.compile(r"""^(?:
(?P<address>
    (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |         # IPv4 address
    (?P<ipv6>\[[a-fA-F0-9:]+\]) |               # IPv6 address
    (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*) # FQDN
):)?(?P<port>\d+)$""", re.X)

class BaseRunTornadoCommand(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--noreload', action='store_false', dest='use_reloader', default=True, help='Tells Django to NOT use the auto-reloader.'),
        make_option('--nocomet', action='store_false', dest='is_comet', default=True, help='Disable comet handlers.'),
        make_option('--nodjango', action='store_false', dest='is_django', default=True, help='Disable django handlers.'),
        make_option('--nossl', action='store_false', dest='is_ssl', default=True, help='Disable SSL support.'),
    )
    help = 'Starts a tornado web server.'
    args = '[optional port number]'
    requires_model_validation = False

    def __init__(self):
        self.address = ''
        self.port = 0
        super(BaseRunTornadoCommand, self).__init__()

    def handle(self, address_port='', *args, **options):
        if address_port:
            matches = re.match(address_port_re, address_port)
            if matches is None:
                raise CommandError('"%s" is not a valid port number or address:port pair.' % address_port)
            address, ipv4, ipv6, fqdn, port = matches.groups()
            if not port.isdigit():
                raise CommandError('%r is not a valid port number.' % port)

            if address:
                if ipv6:
                    address = address[1:-1]
                self.address = address
            self.port = int(port)

        self.run(*args, **options)

    def run(self, *args, **options):
        use_reloader = options.get('use_reloader', True)
        if use_reloader:
            autoreload.main(self.inner_run, args, options)
        else:
            self.inner_run(*args, **options)

    def inner_run(self, *args, **options):
        from django.conf import settings
        from comet.application import Application
        import tornado.ioloop
        import tornado.httpserver

        port = self.port or getattr(settings, 'SERVER_PORT', 8000)
        address = self.address or getattr(settings, 'SERVER_ADDRESS', '')

        # validate models
        self.stdout.write("Validating models...\n\n")
        self.validate(display_num_errors=True)

        self.stdout.write((
            "Django version %(version)s, using settings %(settings)r\n"
            "Development server is running at http://%(address)s:%(port)s/\n"
            "Quit the server with CONTROL-C.\n"
        ) % {
            "version": self.get_version(),
            "settings": settings.SETTINGS_MODULE,
            "address": address or '*',
            "port": port,
        })

        # prepare options
        http_server_options = dict()

        is_ssl = options.get('is_ssl', True)

        if is_ssl and getattr(settings, 'SERVER_SSL_CERT', False) and getattr(settings, 'SERVER_SSL_KEY', False):
            http_server_options['ssl_options'] = {
                'certfile': settings.SERVER_SSL_CERT,
                'keyfile': settings.SERVER_SSL_KEY,
            }

        is_comet = options.get('is_comet', True)
        is_django = options.get('is_django', True)

        # start the server
        application = Application(is_comet=is_comet, is_django=is_django)
        http_server = tornado.httpserver.HTTPServer(application, **http_server_options)
        http_server.listen(port, address=address)
        tornado.ioloop.IOLoop.instance().start()

class Command(BaseRunTornadoCommand):
    pass

