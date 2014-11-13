
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

import re
import os

from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import helper
from tempest.scenario.midokura import manager
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)
# path should be described in tempest.conf
SCPATH = "/network_scenarios/"


class TestNetworkBasicMultitenants(manager.AdvancedNetworkScenarioTest):
    """
        Description:
        Overlapping IP in different tenants

        Scenario:
        VMs with overlapping ip address in different
        tenants should not interfare each other

        Prerequisites:
        - 2 tenants
        - 1 network for each tenant
        - 1 subnet with same CIDR for each tenant

        Steps:
        This testing requires that an option
        "allow_overlapping_ips = True
        " is configured in neutron.conf file

        1. launch VMs with overlapping IP
        2. make sure they are not interfered

        Expected result:
        should succeed
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicMultitenants, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkBasicMultitenants, self).setUp()
        self.scenarios = self.setup_topology(
            os.path.abspath('{0}scenario_basic_multitenant.yaml'.format(SCPATH)))

    def _route_and_ip_test(self, hops):
        LOG.info("Trying to get the list of ips")
        try:
            ssh_client = self.setup_tunnel(hops)
            net_info = ssh_client.get_ip_list()
            LOG.debug(net_info)
            pattern = re.compile(
                '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
            list = pattern.findall(net_info)
            LOG.debug(list)
            remote_ip, _ = hops[-1]
            self.assertIn(remote_ip, list)
            route_out = ssh_client.exec_command("sudo /sbin/route -n")
            self._check_default_gateway(route_out, remote_ip)
            LOG.info(route_out)
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _check_default_gateway(self, route_out, internal_ip):
        try:
            rtable = helper.Routetable.build_route_table(route_out)
            LOG.debug(rtable)
            self.assertTrue(any([r.is_default_route() for r in rtable]))
        except Exception as inst:
            LOG.info(inst.args)
            raise

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_multitenant(self):
        for scenario in self.scenarios:
            self._multitenant_test(scenario)

    def _multitenant_test(self, servers_and_keys):
        ssh_login = CONF.compute.image_ssh_user
        # the access_point server should be the last one in the list
        for element in servers_and_keys:
            ip_address = element['FIP'].floating_ip_address
            private_key = element['keypair']['private_key']
            linux_client = \
                self.get_remote_client(ip_address, ssh_login, private_key)
            result = \
                linux_client.exec_command(
                        "curl http://169.254.169.254/" +
                        "latest/meta-data/instance-id")
            LOG.info(result)
            server = element['server']
            import ipdb; ipdb.set_trace()
            self.assertEqual(server['id]'],result)
        LOG.info("test finished, tearing down now ....")
