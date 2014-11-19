#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest import auth
from tempest import clients
from tempest.common.utils import data_utils


class TenantAdmin(object):
    _interface = 'json'

    def __init__(self):
            _os = clients.AdminManager(interface=self._interface)
            self.client = _os.identity_client

    def tenant_create_enabled(self, name=None, desc=None):
        # Create a tenant that is enabled
        if not name:
            name = data_utils.rand_name(name='tenant-')
        if not desc:
            desc = data_utils.rand_name('desc_')
        resp, tenant = self.client.create_tenant(
            name=name,
            description=desc,
            enabled=True)
        user = self.get_user_by_name('admin')
        role = self.get_role_by_name('admin')
        _, role = self.client.assign_user_role(tenant['id'],
                                               user['id'],
                                               role['id'])
        creds = self._get_credentials(user, tenant)
        return tenant, creds

    def admin_credentials(self, tenant):
        user = self.get_user_by_name('admin')
        return self._get_credentials(user, tenant)

    def _get_credentials(self, user, tenant):
        return auth.get_credentials(
            username=user['name'], user_id=user['id'],
            tenant_name=tenant['name'], tenant_id=tenant['id'],
            password=self.client.password)

    def get_user_by_name(self, name):
        _, users = self.client.get_users()
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    def get_role_by_name(self, name):
        _, roles = self.client.list_roles()
        role = [r for r in roles if r['name'] == name]
        if len(role) > 0:
            return role[0]

    def get_tenant(self, tenant_id):
        res, tenant = self.client.get_tenant(tenant_id)
        return tenant

    def get_tenant_by_name(self, tenant_name):
        tenant = None
        try:
            tenant = self.client.get_tenant_by_name(tenant_name)
        except:
            pass
        return tenant

    def teardown_all(self, tenant):
        self.client.delete_tenant(tenant['id'])
