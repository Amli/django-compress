# -*- coding: utf-8 -*-
try:
  import json
except ImportError:
  import simplejson as json

import httplib, urllib, sys
from django.conf import settings
from compress.filter_base import FilterBase, FilterError

JS_ARGUMENTS = getattr(settings, 'COMPRESS_CLOSURE_JS_ARGUMENTS', '')

def format_compiler_errors(errors_dict):
  errors = []
  for error in errors_dict:
    errors.append("line %d,%d \"%s\"\n%s\n" % (error.get('lineno'), error.get('charno'), error.get('line'), error.get('error', error.get('warning'))))
  return "\n".join(errors)

class ClosureCompilerApiFilter(FilterBase):
  def filter_js(self, js):
    # Define the parameters for the POST request and encode them in
    # a URL-safe format.
    params = urllib.urlencode([
      ('js_code', js),
      ('compilation_level', 'SIMPLE_OPTIMIZATIONS'),
      ('output_format', 'json'),
      ('output_info', 'compiled_code'),
      ('output_info', 'errors'),
      ('output_info', 'warnings'),
      ('output_info', 'statistics'),
    ])

    # Always use the following value for the Content-type header.
    headers = { "Content-type": "application/x-www-form-urlencoded" }
    conn = httplib.HTTPConnection('closure-compiler.appspot.com')
    conn.request('POST', '/compile', params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close

    decoded = json.loads(data)

    if (decoded.get('serverErrors')):
      raise FilterError("%s" % decoded.get('serverErrors'))

    if self.verbose and decoded.get('warnings'):
      print format_compiler_errors(decoded.get('warnings'))

    if (decoded.get('errors')):
      raise FilterError(format_compiler_errors(decoded.get('errors')))

    return decoded.get('compiledCode')
