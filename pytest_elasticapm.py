# -*- coding: utf-8 -*-

import sys
import pytest
from _pytest.reports import CollectReport, TestReport
from _pytest.config import Config
import elasticapm as e_
from typing import Tuple, Optional, Union
from elasticapm.conf.constants import OUTCOME

def _apm_client(client=None) -> e_.Client:
    """
    There may be a level of hell reserved for those doing this
    but it seems that there is no blessed way to maintain state for a pytest
    plugin throughout its lifetime. This works, but a cleaner approach
    would be very welcome.
    """
    if client:
        sys.modules[__name__]._APM_CLIENT = client
    elif not hasattr(sys.modules[__name__], '_APM_CLIENT'):
        sys.modules[__name__]._APM_CLIENT = None
    return sys.modules[__name__]._APM_CLIENT

def pytest_addoption(parser):
    group = parser.getgroup('elasticapm')
    group.addoption(
        '--elastic-apm-server-url',
        action='store',
        dest='dest_elastic_apm_server_url',
        help='Set the URL for the Elastic APM Agent to send data to'
    )

    #parser.addini('HELLO', 'Dummy pytest.ini setting')
def pytest_configure(config):
    # FIXME set url correctly
    client = _apm_client(e_.Client(service_name="testme", server_url="http://localhost:8200")) 

def pytest_sessionstart(session: pytest.Session) -> None:
    client = _apm_client()
    client.begin_transaction(transaction_type=session.name)

def pytest_sessionfinish(session: pytest.Session, exitstatus: Union[int, pytest.ExitCode]) -> None:
    client = _apm_client()
    client.end_transaction(name=session.name)

#def pytest_runtest_protocol(item: pytest.Item, nextitem: Optional[pytest.Item]) -> Optional[object]:
#    pass

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: Optional[pytest.Item]):
    with e_.capture_span(item.name):
        print("sending")
        yield

def pytest_report_teststatus(report: Union[CollectReport, TestReport], config: Config):
    if report.outcome == "failed":
        # FIXME might need to make sure we are in a specific test transaction
        e_.set_transaction_outcome(OUTCOME.FAILURE)
