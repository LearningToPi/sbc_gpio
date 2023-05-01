'''
Base test classes used to represent the test results as well as a structure for the tests.

'''
import logging
from logging_handler import create_logger, DEBUG, INFO, ERROR, WARNING, CRITICAL
from time import time, sleep
import threading


class DevTest_Results:
    ''' 
    Base class to represent the results of a test.

    Properties:
      iterations: (int) total number of tests that were run
      iter_success: (int) number of successful tests that were run
      parameters: (dict) parameters that were used for the test
      start_time: (int) unix time when test was started
      end_time: (int) unix time when test completed
      pass_threshold: (int) percentage required to qualify as successful
      pass_on_zero: (bool) allow a pass if zero successful iterations
      name: (str) Name of the test
      description: (str) Descrption of the test
      details: [list of str] Additional testing data
      passed: (bool) true/false if met pass threshold
      pass_percent: (float) decimal rounded to 2 for the pass rate

    Methods:
    str(DevTest_Results) - Prints the results of the test as a string
    bool(DevTest_Results) - returns True/False if the test passed
    '''
    iterations = None
    iter_success = None
    parameters = {}
    start_time = None
    end_time = None
    pass_threshold = 0
    pass_on_zero = False
    name = ''
    description = ''
    details= []

    def __init__(self, **kwargs):
        ''' 
        All passed kwargs are assigned to the local class fields. The following are used:
        iterations (number of tests run), iter_success (number of successful runs), parameters
        (dict of test parameters), start_time (unix start time), end_time (unix end time),
        pass_threshold (percentage required for test to pass), pass_on_zero (allow a pass if
        there were zero successful iterations), name (name of test), description (description 
        of test), details (list of strings, additional test detailed output if needed) 
        '''
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    @property
    def passed(self):
        ''' return True/False if the test passed '''
        if self.end_time and self.iterations and self.iter_success and self.pass_threshold:
            return self.iter_success / self.iterations >= self.pass_threshold
        if self.pass_on_zero and self.pass_threshold == 0:
            return True
        return False
    
    @property
    def pass_percent(self):
        ''' Return the pass percentage '''
        if self.end_time and self.iterations and self.iter_success and self.pass_threshold:
            return round(self.iter_success / self.iterations, 2)
        if self.pass_on_zero and self.pass_threshold == 0:
            return 1
        return 0
        
    def __str__(self):
        return f"Test {self.name} {'PASSED' if self.passed else 'FAILED'}: {self.iter_success} / {self.iterations} iterations successful. " \
               f"{self.pass_percent * 100}%, pass theshold is {self.pass_threshold * 100}%"
    
    def __bool__(self):
        return self.passed


class DevTest_Base:
    ''' Base class to represent a test.  Will be overriden be specific test cases '''
    def __init__(self, log_level=INFO):
        self._logger = create_logger(console_level=log_level, name=self.info_str)
        self._stop_tests = False
        self._testing_lock = threading.Lock()
        self._testing_thread = None

    def __del__(self):
        self.close()

    def close(self):
        ''' Close and clean up any objects '''
        pass

    @property
    def info_str(self):
        """ Returns the info string for the class (used in logging commands) """
        return f"{self.__class__.__name__}"

    @property
    def is_running(self):
        ''' Return True/False if a test is running '''
        return self._testing_lock.locked()
    
    def stop(self, wait=False, timeout=10):
        ''' Stop any test in process '''
        if self.is_running:
            self._logger.info(f"{self.info_str}: Sent stop request to test. Timeout {timeout}...")
            self._stop_tests = True
            if wait:
                cancel_time = time() + timeout
                while self.is_running:
                    sleep(.25)

    @property
    def is_test_ok(self):
        ''' Check if the system is able to run the test '''
        pass

    def config_test(self):
        ''' Provide configuration to the test (may also be passed during init)'''
        pass


    def start(self, run_secs=10, iterations=None, wait=False, asyncio=False, **kwargs):
        ''' Start the test '''
        if not self.is_test_ok:
            raise ImportError(f"{self.info_str}: Unable to start test")
        self.test_results = None
        if iterations is not None:
            self._logger.info(f"{self.info_str}: Running test with {iterations} iterations. Wait: {wait}. Other Args: {kwargs}")
            if wait:
                self._start_thread_iterations(iterations=iterations, run_secs=run_secs, **kwargs)
            else:
                if not self.is_running:
                    pass_kwargs = {'iterations': iterations, 'run_secs': run_secs}
                    pass_kwargs.update(kwargs)
                    self._testing_thread = threading.Thread(target=self._start_thread_iterations, kwargs=pass_kwargs, name=self.info_str)
                    self._testing_thread.start()
                else:
                    self._logger.warning(f"{self.info_str}: Unable to start threaded test as another test is currently running.")
        else:
            self._logger.info(f"{self.info_str}: Running test for {run_secs} seconds. Wait: {wait}. Other Args: {kwargs}")
            if wait:
                self._start_thread_time(run_secs=run_secs, **kwargs)
            else:
                if not self.is_running:
                    pass_kwargs = {'iterations': iterations, 'run_secs': run_secs}
                    pass_kwargs.update(kwargs)
                    self._testing_thread = threading.Thread(target=self._start_thread_time, kwargs=pass_kwargs, name=self.info_str)
                    self._testing_thread.start()
                else:
                    self._logger.warning(f"{self.info_str}: Unable to start threaded test as another test is currently running.")

    def _start_thread_iterations(self, iterations, run_secs):
        pass

    def _start_thread_time(self, run_secs, iterations):
        pass