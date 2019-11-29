
#!/usr/bin/env python

import os, sys 
from snap import snap
from snap import core
import json
from snap.loggers import transform_logger as log


CHIME_SPECIAL_API_KEY='eyJhbGciOiJIUzI1NiJ9.eyJleHQiOjMwNzUzODI5MTQwNTUsInVzZXJfaWQiOjM1ODUzMTI0ODA5NTExMCwic2NvcGUiOiI1IiwiaWF0IjoxNDk4NTgyOTE0MDU1fQ.LwMpLHFK10uYJyMjNUnZ3dSHK_dKaU9AoU_dlQQ1CWQ'


def ping_func(input_data, service_objects, **kwargs):
    return core.TransformStatus(json.dumps({'message': 'LeadListener is alive.'}))


def new_lead_func(input_data, service_objects, **kwargs):
    '''
    zillow_api = service_objects.lookup('zillow')
    street_address = input_data['address']
    city = input_data['city']
    state= = input_data['state']
    zip_code = input_data['zip']
    zapi.lookup_address(address='1349 Pacific Street', city='Brooklyn', state='NY', zip_code='11216')
    '''
    print(json.dumps(input_data), file=sys.stderr)
    return core.TransformStatus(json.dumps({'message': 'New lead entered into CHIME!', 'data': json.dumps(input_data)}))



