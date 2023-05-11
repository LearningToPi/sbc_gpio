from ._test_base import DevTest_Base, DevTest_Results, DEBUG, INFO, ERROR, WARNING, CRITICAL
import os
import subprocess
import socket
import lirc
from collections import namedtuple
from time import time, sleep
import re

TEST_NAME = 'IR GPIO TX/RX'
TEST_DESCRIPTION = 'Uses lirc with an infrared LED and receiver to test sending and receiving IR signals.'
PASS_THRESHOLD = 0.75

LIRC_DEVS = namedtuple("LIRC_DEVS", ("tx", "rx"))
LIRC_REMOTE = namedtuple("LIRC_REMOTE", ('name', 'keys'))

LIRC_DEVICE_PATH = '/tmp/'

LIRC_REMOTE_FILE = os.path.join(os.path.dirname(__file__), 'lirc', 'aa59-00741a.lircd.conf')
LIRC_EXCLUDE_REMOTES = ['devinput-32', 'devinput-64']


def get_pid_list(filter_list:list) -> list:
    ''' Get a list of running pids and return the pid matching the list of regex filters '''
    ps_list = subprocess.run('ps aux'.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return_pids = [None] * len(filter_list)
    for process_line in ps_list.stdout.decode('utf-8').split('\n'):
        for filter in filter_list:
            if re.search(filter, process_line):
                return_pids[filter_list.index(filter)] = process_line.split()[1] # type: ignore
    return return_pids

class DevTest_IR(DevTest_Base):
    ''' Class for an IR TX/RX test using lirc and GPIO based IR transmitter and receiver '''
    def __init__(self, log_level=INFO, lircd_path=LIRC_DEVICE_PATH):
        super().__init__(log_level)
        self._ir_ok = None
        self._ir_tx_obj = None
        self._ir_rx_obj = None
        self.ir_tx_dev = None
        self.ir_rx_dev = None
        self.ir_tx_driver = None
        self.ir_rx_driver = None
        self._ir_tx_process = None
        self._ir_rx_process = None
        self.lircd_path = lircd_path

    def close(self):
        # kill lircd processes if started by devtester
        if self._ir_tx_process is not None:
            lircd_procs = get_pid_list([f"lircd.*{self.ir_tx_dev}"])
            for process in lircd_procs:
                if process is not None:
                    self._logger.info(f"{self.info_str}: lircd TX process pid: {self._ir_tx_process.pid} stopping...")
                    subprocess.run(f'kill {process}'.split())
        if self._ir_rx_process is not None:
            lircd_procs = get_pid_list([f"lircd.*{self.ir_rx_dev}"])
            for process in lircd_procs:
                if process is not None:
                    self._logger.info(f"{self.info_str}: lircd RX process pid: {self._ir_rx_process.pid} stopping...")
                    subprocess.run(f'kill {process}'.split())
        sleep(1)
        if self._lircd_rx_proc() or self._lircd_tx_proc():
            raise RuntimeError(f'{self.info_str}: Error terminating lircd processes!')

    @property
    def _ir_tx(self):
        ''' Return the TX LIRC object '''
        if isinstance(self._ir_tx_obj, lirc.Client):
            return self._ir_tx_obj
        if self.is_test_ok:
            self._ir_tx_obj = lirc.Client(lirc.LircdConnection(address=self.lircd_path + self.ir_tx_dev)) # type: ignore
            return self._ir_tx_obj
        raise LookupError(f'{self.info_str}: Unable to open TX IR device')

    @property
    def _ir_rx(self):
        ''' Return the RX socket '''
        if isinstance(self._ir_rx_obj, socket.socket):
            return self._ir_rx_obj
        if self.is_test_ok:
            self._ir_rx_obj = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._ir_rx_obj.connect(self.lircd_path + self.ir_rx_dev) # type: ignore
            self._ir_rx_obj.setblocking(False)
            return self._ir_rx_obj
        raise LookupError(f'{self.info_str}: Unable to open RX IR device')
    
    @property
    def _remote_codes(self) -> tuple:
        ''' Return a tuple containing the remote and keys for all remotes available to LIRCD and associated tuple containing all codes '''
        raw_remotes = self._ir_tx.list_remotes()
        if isinstance(raw_remotes, list):
            remotes = tuple([LIRC_REMOTE(x, tuple([y.split()[1] for y in self._ir_tx.list_remote_keys(x)])) for x in raw_remotes if x not in LIRC_EXCLUDE_REMOTES])
        elif isinstance(raw_remotes, str):
            remotes = tuple([LIRC_REMOTE(raw_remotes, tuple([y.split()[1] for y in self._ir_tx.list_remote_keys(raw_remotes)]))])
        else:
            raise ValueError(f'Unable to query remotes from {self.ir_tx_dev}.  Received a {type(raw_remotes)}, expected a list or string.')
        if len(remotes) == 0:
            raise ValueError(f"{self.info_str}: Unable to identify any configured remote controls")
        return remotes

    @property
    def is_test_ok(self):
        ''' Checks if there are 2 IR devices, one using send and one receive '''
        if self._ir_ok is not None:
            return self._ir_ok
        try:
            lirc_sys = os.listdir('/sys/class/lirc')
            if len(lirc_sys) < 2:
                self._logger.warning(f"{self.info_str}: Insufficient lirc devices.  Skipping all IR tests.")
                self._ir_ok = False
            for lirc_dev in lirc_sys:
                driver_path = os.path.realpath(f'/sys/class/lirc/{lirc_dev}/device/device')
                driver_name = driver_path.rsplit('/', 1)[1]
                device = {'os_driver': driver_name}
                if 'tx' in driver_name or 'transmit' in driver_name:
                    device['dir'] = 'out'
                    self.ir_tx_dev = lirc_dev
                    self.ir_tx_driver = driver_name
                elif 'rx' in driver_name or 'recv' in driver_name or 'receiver' in driver_name:
                    device['dir'] = 'in'
                    self.ir_rx_dev = lirc_dev
                    self.ir_rx_driver = driver_name
                else:
                    raise AttributeError(f'Unable to determine direction of {lirc_dev}')
            
            # make sure there is at least 1 send and 1 recieve device
            if self.ir_tx_dev is not None and self.ir_rx_dev is not None:
                self._ir_ok = True
                return True
            return False

        except Exception as e:
            self._logger.warning(f"{self.info_str}: Unable to list lirc devices.  Skipping all IR tests: {e}")
            self._ir_ok = False

    def _lircd_tx_proc(self) -> bool:
        ''' Check if lircd tx process started by the devtest python is up '''
        if not self.is_test_ok:
            return False
        if self._ir_tx_process and self._ir_tx_process.poll() is None:
            # process started by devtest
            return True
        if get_pid_list([f"lircd.*{self.ir_tx_dev}"])[0] != None:
            # other lircd process started outside of devtest for the device specified
            return True
        return False
        
    def _lircd_rx_proc(self) -> bool:
        ''' Check if lircd rx process started by the devtest python is up '''
        if not self.is_test_ok:
            return False
        if self._ir_rx_process and self._ir_rx_process.poll() is None:
            return True
        if get_pid_list([f"lircd.*{self.ir_rx_dev}"])[0] != None:
            # other lircd process started outside of devtest for the device specified
            return True
        return False
    
    def lirc_start(self):
        ''' Starts the lirc daemon for the TX and RX '''
        if not self.is_test_ok:
            self._logger.warning(f"{self.info_str}: Unable to start IR devices.  All IR tests skipped.")
            return False
        
        # check if lirc processes are already running
        try:
            if not self._lircd_tx_proc():
                # start the lircd TX process
                self._logger.info(f"{self.info_str}: lircd TX process starting...")
                self._ir_tx_process = subprocess.Popen(f"/sbin/lircd --driver=default --device=/dev/{self.ir_tx_dev} --output={self.lircd_path + self.ir_tx_dev} --pidfile={self.lircd_path + self.ir_tx_dev}.pid --nodaemon {LIRC_REMOTE_FILE}".split(),  # type: ignore
                                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                # wait 1 second and make sure the process didn't terminate
                sleep(1)
                if self._ir_tx_process.poll() != None:
                    stdout, stderr = self._ir_tx_process.communicate()
                    self._logger.error(f"{self.info_str}: Error starting LIRC TX process. code: {self._ir_tx_process.poll()}, stdout: {stdout}, stderr: {stderr}")
                    self._ir_tx_process = None
                else:
                    self._logger.info(f"{self.info_str}: lircd TX process pid: {self._ir_tx_process.pid}")
                
            if not self._lircd_rx_proc():
                # start the lircd RX process
                self._logger.info(f"{self.info_str}: lircd RX process starting...")
                self._ir_rx_process = subprocess.Popen(f"/sbin/lircd --driver=default --device=/dev/{self.ir_rx_dev} --output={self.lircd_path + self.ir_rx_dev} --pidfile={self.lircd_path + self.ir_rx_dev}.pid --nodaemon {LIRC_REMOTE_FILE}".split(),  # type: ignore
                                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                # wait 1 second and make sure the process didn't terminate
                sleep(1)
                if self._ir_rx_process.poll() != None:
                    stdout, stderr = self._ir_rx_process.communicate()
                    self._logger.error(f"{self.info_str}: Error starting LIRC TX process. code: {self._ir_rx_process.poll()}, stdout: {stdout}, stderr: {stderr}")
                    self._ir_rx_process = None
                else:
                    self._logger.info(f"{self.info_str}: lircd RX process pid: {self._ir_rx_process.pid}")

            if not self._lircd_tx_proc() or not self._lircd_rx_proc():
                raise ConnectionError(f"{self.info_str}: Unable to start lircd IR processes")
        
        except Exception as e:
            raise ConnectionError(f"{self.info_str}: Unable to start lircd IR processes")

    def lirc_stop(self, force=False):
        ''' Stops the lirc daemon for the TX and RX. '''
        self.close()

    def _transmit_blocking(self, remote, key, tx_ms, wait_delay_ms=100) -> str:
        ''' Send the IR command and validate response.  Return received string '''
        self._logger.debug(f"{self.info_str}: IR Test: Sending {remote} {key}")
        self.lirc_rx_read_code() # Read from the RX to clear any stored codes
        self._ir_tx.send_start(remote, key)
        sleep(tx_ms / 1000)
        self._ir_tx.send_stop(remote, key)
        sleep(wait_delay_ms / 1000)
        recv = self.lirc_rx_read_code()
        self._logger.debug(f"{self.info_str}: IR Test: Received {recv}")
        return recv

    def _start_thread_iterations(self, iterations, tx_ms=1000, delay_ms=250, run_secs=None):
        ''' Run the IR test threaded or blocking '''
        with self._testing_lock:
            self.lirc_start()
            remote_list = self._remote_codes
            iter_run, iter_success = 0, 0
            self.lirc_rx_read_code() # read from the RX stream to clear any pending data
            start_time = time()
            try:
                while iter_run < iterations and not self._stop_tests:
                    for remote in remote_list:
                        for key in remote.keys:
                            iter_run += 1
                            recv = self._transmit_blocking(remote.name, key, tx_ms)
                            if recv == key:
                                iter_success += 1
                            else:
                                self._logger.warning(f"{self.info_str}: IR Test: Failed reading {remote.name} {key}.  Recived: {recv}")
                            if self._stop_tests or iter_run >= iterations:
                                raise StopIteration
                            sleep(delay_ms / 1000)
            except StopIteration:
                pass
            except Exception as e:
                self._logger.error(f"{self.info_str}: IR Test: Error during test loop: {e}")
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'iterations': iterations, 'tx_ms': tx_ms, 'delay_ms':delay_ms,
                                                            'ir_tx_driver': self.ir_tx_driver, 'ir_rx_driver': self.ir_rx_driver},
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)

    def _start_thread_time(self, run_secs=10, tx_ms=1000, delay_ms=250, iterations=None):
        ''' Run the IR test threaded or blocking '''
        with self._testing_lock:
            self.lirc_start()
            remote_list = self._remote_codes
            iter_run, iter_success = 0, 0
            self.lirc_rx_read_code() # read from the RX stream to clear any pending data
            start_time = time()
            stop_time = time() + run_secs
            try:
                while time() < stop_time and not self._stop_tests:
                    for remote in remote_list:
                        for key in remote.keys:
                            iter_run += 1
                            recv = self._transmit_blocking(remote.name, key, tx_ms)
                            if recv == key:
                                iter_success += 1
                            else:
                                self._logger.warning(f"{self.info_str}: IR Test: Failed reading {remote.name} {key}.  Recived: {recv}")
                            if self._stop_tests or time() >= stop_time:
                                raise StopIteration
                            sleep(delay_ms / 1000)
            except StopIteration:
                pass
            except Exception as e:
                self._logger.error(f"{self.info_str}: IR Test: Error during test loog: {e}")
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'run_secs': run_secs, 'tx_ms': tx_ms, 'delay_ms':delay_ms,
                                                            'ir_tx_driver': self.ir_tx_driver, 'ir_rx_driver': self.ir_rx_driver},
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)

    def lirc_rx_read_code(self) -> str:
        ''' Read any pending data from the socket and return the last code received '''
        try:
            data = self._ir_rx.recv(8192)
            return data.decode('utf-8').strip().split('\n')[-1].split()[-2]
        except BlockingIOError:
            return 'NO-DATA'