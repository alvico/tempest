# Ensure cirros 0.3.3 is the image in tempest
# Ensure that allow overlapping tenants is set to false?
# tempest.con is configured properly, and tenants are clean

import glanceclient.v2.client as glclient
import keystoneclient.v2_0.client as ksclient
import os

from simpleconfigparser import simpleconfigparser
from tempest import clients
from tempest.scenario.midokura.midotools import admintools
from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)


def main(self):
    admin = admintools.TenantAdmin()
    tenant_name = CONF.intdentity.admin_tenant_name
    self.tenant = admin.get_tenant_by_name(tenant_name)
    credentials = admin.admin_credentials(self.tenant)
    self.set_context(credentials)
    self.image_ref = None

    # Start to config
    self.fix_cirros()
    self.fix_tempest_conf()


def set_context(self, credentials):
    keystone = ksclient.Client(**self._get_keystone_credentials(credentials))
    self.manager = clients.Manager(credentials=credentials)
    self.network_client = self.manager.network_client
    self.image_client = self.manager.image_client
    glance_endpoint = keystone.service_catalog.url_for(service_type='image',
                                                       endpoint_type='internal')
    self.glance_client =\
        glclient.Client(glance_endpoint,
                        token=keystone.auth_token)


def _get_keystone_credentials(self, credentials):
    d = {}
    d['username'] = credentials.username
    d['password'] = credentials.password
    d['auth_url'] = CONF.identity.uri
    d['tenant_name'] = credentials.tenant_name
    d['endpoint_type'] = 'public'
    return d


def fix_cirros(self):
    images = self.glance_client.images.list()
    flag = 1
    for img in images:
        if img['checksum'] == '133eae9fb1c98f45894a4e60d8736619' and img[
                'visibility'] is 'public':
            self.image_ref = img['id']
            flag = 0
            break
    if flag > 0:
        self.upload_cirros()


def upload_cirros(self):
    # create and image with cirros 0.3.3
    kwargs = {
        'location': 'http://download.cirros-cloud.net/0.3.3/cirros-0.3.3-x86_64-disk.img',
        'visibility': 'public',
        'is_public': True,
    }
    resp, body = self.image_client.create_image(name='cirros 0.3.3',
                                                container_format='bare',
                                                disk_format='raw',
                                                **kwargs)
    if resp['status'] != "201":
        raise Exception("Cirros image not created")
    else:
        self.image_ref = body['id']


def fix_tempest_conf(self):
    DEFAULT_CONFIG_DIR = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "etc")

    DEFAULT_CONFIG_FILE = "/tempest.conf"
    _path = DEFAULT_CONFIG_DIR + self.DEFAULT_CONFIG_FILE
    if not os.path.isfile(_path):
        raise Exception("No config file in %s", _path)

    config = simpleconfigparser()
    config.read(_path)

    # get neutron suported extensions
    _, extensions_dict = self.network_client.list_extensions()
    extensions = [x['name'] for x in extensions_dict['extensions']]

    # setup network extensions
    if CONF.network_feature_enabled.api_extensions != extensions:
        # modify tempest.conf file
        to_string = ""
        for ex in extensions[:-1]:
            to_string = str.format("{0},{1}", ex, to_string)
        to_string = str.format("{0}{1}", to_string, extensions[-1])
        config.set('network-feature-enabled',
                   'api_extensions', to_String)

    # set up image_ref
    if self.image_ref:
        config.set('compute', 'image_ref', self.image_ref)

    # set up allow_tenant_isolation
    try:
        if not config.get('auth', 'allow_tenant_isolation'):
            config.set('auth', 'allow_tenant_isolation', 'True')
    execpt:
        if not config.get('compute', 'allow_tenant_isolation'):
            config.set('compute', 'allow_tenant_isolation', 'True')

    with open(_path, 'w') as tempest_conf:
        config.write(tempest)


if __name__ == "__main__":
    main()
