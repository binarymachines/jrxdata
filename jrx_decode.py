#!/usr/bin/env python

import json
from snap.loggers import request_logger as log


def decode_json(http_request):
    log.info('>>> Invoking custom request decoder.')
    decoder_output = {}
    decoder_output.update(http_request.get_json(silent=True))
    return decoder_output