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

NODE_ID = 11223344
SETUPPINCODE = 20202021
DISCRIMINATOR = 3840
CHIP_PORT = 5540
CIRQUE_URL = "http://localhost:5000"
CHIP_REPO = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "..", "..", "..")

DEVICE_CONFIG = {
    'device0': {
        'type': 'Android-server',
        'base_image': 'connectedhomeip/chip-build-android',
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

    def _run_android_app(self, server_ids: list) -> None:
        app_path = os.path.join(
            CHIP_REPO, "out/debug/standalone/chip-all-clusters-app")
        command = f"CHIPCirqueDaemon.py -- run {app_path}"
        for server_id in server_ids:
            self.execute_device_cmd(server_id, command)

    def _get_devices_information(self) -> dict:
        result = dict({"Android-server": dict(), "CHIP-Tool": dict()})
        for device in self.non_ap_devices:
            if (x := device["type"]) in result.keys():
                result[x][device["id"]] = {
                    "ipv6": device["description"]["ipv6_addr"]}
        return result

    def _get_test_command_list(self) -> list:
        # chip-tool lowpower sleep 1 0
        chip_tool_path = os.path.join(
            CHIP_REPO, "out/debug/standalone/chip-tool")
        on_off_command = f"{chip_tool_path} onoff {'{}'} {NODE_ID} 1"
        result = [
            ("pairing", f"{chip_tool_path} pairing ethernet {NODE_ID} {SETUPPINCODE} {DISCRIMINATOR} {'{ip}'} {CHIP_PORT}"),
            #("on", on_off_command.format("on")),
            #("off", on_off_command.format("off")),
            ("sleep", f"{chip_tool_path} lowpower sleep {NODE_ID} 1"),
            ("get MAC",
             f"{chip_tool_path} wakeonlan read wake-on-lan-mac-address {NODE_ID} 1"),
            #("playback-state",f"{chip_tool_path} mediaplayback read playback-state {NODE_ID} 3"),
            ("paring unpair", f"{chip_tool_path} pairing unpair {NODE_ID}")
        ]
        return result

    def _check_device_log(self, server_ids) -> None:
        fail_meg = "Media Cluster test failed: cannot find matching string from device {}"
        check_point = [
            "Received spake2p msg1",
            "Sent spake2p msg2",
            "Received spake2p msg3"
        ]
        for device_id in server_ids:
            device_log = self.get_device_log(device_id).decode('utf-8')
            self.logger.info(
                f"checking device log for {self.get_device_pretty_id(device_id)}")
            self.assertTrue(
                self.sequenceMatch(device_log, check_point),
                fail_meg.format(device_id)
            )

    def _run_test_command(self, tool_device_id, server_ip_address) -> None:
        command_list = self._get_test_command_list()
        fail_meg = "{} command failure: {}"
        for ip in server_ip_address:
            for name, cmd in command_list:
                ret = self.execute_device_cmd(
                    tool_device_id, cmd.format(ip=ip))
                self.assertEqual(ret['return_code'], '0',
                                 fail_meg.format(name, ret['output']))

    def run_media_cluster_test(self):
        devices_information = self._get_devices_information()
        server_ids = list(devices_information["Android-server"].keys())
        tool_device_id = list(devices_information["CHIP-Tool"].keys())[0]
        server_ip_address = [x["ipv6"]
                             for x in devices_information["Android-server"].values()]

        self._run_android_app(server_ids)
        self._run_test_command(tool_device_id, server_ip_address)
        self._check_device_log(server_ids)


if __name__ == "__main__":
    sys.exit(TestAndroidMediaCluster(DEVICE_CONFIG).run_test())
