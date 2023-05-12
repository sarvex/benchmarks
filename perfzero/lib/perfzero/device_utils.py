# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Setup the data drive with raid, RAM, or mount network drives."""
from __future__ import print_function

import logging

import perfzero.utils as utils


def create_drive_from_devices(data_dir, gce_nvme_raid):
  """Creates a drive at data directory."""
  if not gce_nvme_raid:
    return

  devices = _get_nvme_devices()
  cmd = f'mountpoint -q {data_dir}'
  retcode, _ = utils.run_command(cmd)
  if retcode:
    if len(devices) > 1:
      _create_drive_raid(data_dir, devices)
    else:
      _create_single_drive(data_dir, devices[0])


def _get_nvme_devices():
  """Returns list paths to nvme devices."""
  devices = []
  cmd = 'lsblk'
  retcode, log = utils.run_command(cmd)
  if retcode:
    raise Exception(f'"{cmd}" failed with code:{retcode} and log:\n{log}')

  if lines := log.splitlines():
    for line in lines:
      if line.startswith('nvme'):
        parts = line.split()
        devices.append(f'/dev/{parts[0].strip()}')
  return devices


def _create_single_drive(data_dir, device):
  """Creates a data drive out of a single device."""
  cmds = [
      f'mkfs.ext4 -F {device}',
      f'mkdir -p {data_dir}',
      f'mount {device} {data_dir}',
      f'chmod a+w {data_dir}',
  ]
  utils.run_commands(cmds)
  logging.info('Created and mounted device %s at %s', device, data_dir)


def _create_drive_raid(data_dir, devices):
  """Creates a raid zero array of nvme drives."""
  cmds = [
      f"yes | mdadm --create /dev/md0 --level=0 --raid-devices={len(devices)} {' '.join(devices)}",
      'mkfs.ext4 -F /dev/md0',
      f'mkdir -p {data_dir}',
      f'mount /dev/md0 {data_dir}',
      f'chmod a+w {data_dir}',
  ]
  utils.run_commands(cmds)
  logging.info('Created and mounted RAID array at %s', data_dir)


