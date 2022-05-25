#
# This file is part of the celery-utils (https://github.com/e.sovetkin/celery-utils).
# Copyright (c) 2022 Jenya Sovetkin.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import re
import bottle
import logging

from cu.app \
    import CONFIGS

logging.basicConfig(**CONFIGS['webserver_logs_kwargs'])

from cu.utils.calldocs \
    import calldocs

from cu.utils.import_function \
    import import_function

from cu.webserver.utils \
    import format_help

from cu.webserver.utils \
    import format_help, return_exception, \
    call_method, parse_args, serve


def _check_allowed(method):
    if not isinstance(CONFIGS['app']['allowed_imports'], list):
        raise RuntimeError\
            ("CONFIGS['app']['allowed_imports'] should be a list!")

    for x in CONFIGS['app']['allowed_imports']:
        if re.match(x, method):
            return True
    return False


def _method2module(method):
    method = method.replace('/','.')
    if not _check_allowed(method):
        raise RuntimeError\
            ('{} does match to the allowed imports!'\
             .format(method))

    return import_function(method)


@bottle.error(404)
def error404(error):
    return {'results': str(error)}


@bottle.route('/api/help/<method:path>', method=['GET'])
def get_help(method):
    res = calldocs(_method2module(method))
    return {'results': format_help(res)}


@bottle.route('/api/<method_str:path>', method=['GET','POST'])
def do_method(method_str):
    if 'GET' == bottle.request.method:
        args = bottle.request.query
    elif 'POST' == bottle.request.method:
        args = bottle.request.json
    else:
        return error404('%s access method is not implemented' \
                        % str(bottle.request.method))

    try:
        method = _method2module(method_str)
        defaults = calldocs(method)['args']
        args = parse_args(data = args, defaults = defaults)
    except Exception as e:
        return return_exception(e)

    # TODO: set correctly the serve_type
    # serve_type = args['serve_type']
    # del args['serve_type']

    # TODO: special treatment should be for /upload
    # bottle.request.files.data to pass to upload() correctly?

    return serve(call_method(method=method_str, args=args),
                 serve_type = 'file')


bottle.run(host=CONFIGS['webserver']['host'],
           port=CONFIGS['webserver']['port'],
           server='gunicorn',
           workers=CONFIGS['webserver']['workers'],
           max_requests=CONFIGS['webserver']['max_requests'],
           timeout=CONFIGS['webserver']['timeout'])