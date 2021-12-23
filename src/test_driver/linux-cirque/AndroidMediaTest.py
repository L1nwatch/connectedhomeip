#!/usr/bin/env python3
"""
Copyright (c) 2021 Project CHIP Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import os
import pprint
import time
import sys

from helper.CHIPTestBase import CHIPVirtualHome

logger = logging.getLogger('AndroidMediaTest')
logger.setLevel(logging.INFO)

sh = logging.StreamHandler()
sh.setFormatter(
    logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s %(message)s'))
logger.addHandler(sh)

SETUPPINCODE = 20202021
DISCRIMINATOR = 1  # Randomw number, not used
CHIP_PORT = 5540
CIRQUE_URL = "http://localhost:5000"
CHIP_REPO = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "..", "..", "..")

DEVICE_CONFIG = {
    'device0': {
        'type': 'Android-server',
        'base_image': 'connectedhomeip/chip-cirque-device-base',
        'capability': ['Interactive', 'TrafficControl', 'Mount'],
        'rcp_mode': True,
        'docker_network': 'Ipv6',
        'traffic_control': {'latencyMs': 100},
        "mount_pairs": [[CHIP_REPO, CHIP_REPO]],
    },
    'device1': {
        'type': 'CHIP-Tool',
        'base_image': 'connectedhomeip/chip-cirque-device-base',
        'capability': ['Thread', 'Interactive', 'TrafficControl', 'Mount'],
        'rcp_mode': True,
        'docker_network': 'Ipv6',
        'traffic_control': {'latencyMs': 100},
        "mount_pairs": [[CHIP_REPO, CHIP_REPO]],
    }
}


class TestAndroidMediaCluster(CHIPVirtualHome):
    def __init__(self, device_config):
        super().__init__(CIRQUE_URL, device_config)
        self.logger = logger

    def setup(self):
        self.initialize_home()

    def test_routine(self):
        self.run_media_cluster_test()

    def run_media_cluster_test(self):
        server_ip_address = set()

        server_ids = [device['id']
                      for device in self.non_ap_devices if device['type'] == 'Android-server']
        tool_ids = [device['id']
                    for device in self.non_ap_devices if device['type'] == 'CHIP-Tool']
        tool_device_id = tool_ids[0]

        for server in server_ids:
            app_path = os.path.join(
                CHIP_REPO, "out/debug/standalone/chip-all-clusters-app")
            self.execute_device_cmd(
                server, f"CHIPCirqueDaemon.py -- run {app_path}")
            server_ip_address.add(self.execute_device_cmd(server, "ipconfig"))
            server_ip_address.add(self.execute_device_cmd(server, "ip r"))
            server_ip_address.add(self.execute_device_cmd(server, "ifconfig"))
        self.logger.info(f"ip address:{server_ip_address}")

        chip_tool_path = os.path.join(
            CHIP_REPO, "out/debug/standalone/chip-tool")
        command = chip_tool_path + " onoff {} 1"
        cmd_fail = "{} command failure: {}"

        for ip in server_ip_address:
            cmd = f"{chip_tool_path} pairing {SETUPPINCODE} {DISCRIMINATOR} {ip} {CHIP_PORT}"
            ret = self.execute_device_cmd(tool_device_id, cmd)
            self.assertEqual(ret['return_code'], '0',
                             cmd_fail.format("pairing", ret['output']))

            ret = self.execute_device_cmd(tool_device_id, command.format("on"))
            self.assertEqual(ret['return_code'], '0',
                             cmd_fail.format("on", ret['output']))

            ret = self.execute_device_cmd(
                tool_device_id, command.format("off"))
            self.assertEqual(ret['return_code'], '0',
                             cmd_fail.format("off", ret['output']))

            ret = self.execute_device_cmd(
                tool_device_id, f"{chip_tool_path} pairing unpair")
            self.assertEqual(ret['return_code'], '0', cmd_fail.format(
                "pairing unpair", ret['output']))

        test_fail = "Media Cluster test failed: cannot find matching string from device {}"
        for device_id in server_ids:
            self.logger.info(
                f"checking device log for {self.get_device_pretty_id(device_id)}")
            self.assertTrue(self.sequenceMatch(self.get_device_log(device_id).decode('utf-8'), ["OnOff"]),
                            test_fail.format(device_id))


if __name__ == "__main__":
    sys.exit(TestAndroidMediaCluster(DEVICE_CONFIG).run_test())
