import pytest as pytest

from common.serializers.serialization import domain_state_serializer
from plenum.common.constants import ROLE, STEWARD, NYM, TARGET_NYM, TXN_TYPE, TXN_AUTHOR_AGREEMENT, \
    TXN_AUTHOR_AGREEMENT_TEXT, TXN_AUTHOR_AGREEMENT_VERSION, TRUSTEE, DOMAIN_LEDGER_ID, GET_TXN_AUTHOR_AGREEMENT, \
    GET_TXN_AUTHOR_AGREEMENT_VERSION, GET_TXN_AUTHOR_AGREEMENT_DIGEST, GET_TXN_AUTHOR_AGREEMENT_TIMESTAMP
from plenum.common.exceptions import UnauthorizedClientRequest, InvalidClientRequest
from plenum.common.request import Request
from plenum.common.txn_util import get_payload_data, reqToTxn, get_reply_nym
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.get_txn_author_agreement_handler import GetTxnAuthorAgreementHandler
from plenum.server.request_handlers.static_taa_helper import StaticTAAHelper
from plenum.server.request_handlers.utils import get_nym_details, get_role, is_steward, nym_to_state_key
from plenum.test.testing_utils import FakeSomething
from state.state import State


@pytest.fixture(scope="function")
def get_txn_author_agreement_handler(tconf):
    data_manager = DatabaseManager()
    handler = GetTxnAuthorAgreementHandler(data_manager, FakeSomething())
    state = State()
    state.txn_list = {}
    state.get = lambda key, isCommitted=False: state.txn_list.get(key, None)
    state.set = lambda key, value, isCommitted=False: state.txn_list.update({key: value})
    data_manager.register_new_database(handler.ledger_id,
                                       FakeSomething(),
                                       state)
    return handler


@pytest.fixture(scope="function")
def get_taa_request(tconf, get_txn_author_agreement_handler):
    return Request(identifier="identifier",
                   operation={TXN_TYPE: GET_TXN_AUTHOR_AGREEMENT,
                              GET_TXN_AUTHOR_AGREEMENT_VERSION: "VERSION"})


def test_static_validation(get_txn_author_agreement_handler):
    request = Request(operation={TXN_TYPE: GET_TXN_AUTHOR_AGREEMENT,
                                 GET_TXN_AUTHOR_AGREEMENT_VERSION: "VERSION"})
    get_txn_author_agreement_handler.static_validation(request)

    request = Request(operation={TXN_TYPE: GET_TXN_AUTHOR_AGREEMENT,
                                 GET_TXN_AUTHOR_AGREEMENT_DIGEST: "DIGEST"})
    get_txn_author_agreement_handler.static_validation(request)

    request = Request(operation={TXN_TYPE: GET_TXN_AUTHOR_AGREEMENT,
                                 GET_TXN_AUTHOR_AGREEMENT_TIMESTAMP: 1559299045})
    get_txn_author_agreement_handler.static_validation(request)


def test_static_validation_with_redundant_fields(get_txn_author_agreement_handler):
    request = Request(operation={TXN_TYPE: GET_TXN_AUTHOR_AGREEMENT,
                                 GET_TXN_AUTHOR_AGREEMENT_VERSION: "VERSION",
                                 GET_TXN_AUTHOR_AGREEMENT_DIGEST: "DIGEST"})
    with pytest.raises(InvalidClientRequest,
                       match="GET_TXN_AUTHOR_AGREEMENT request can have at most one of "
                             "the following parameters: version, digest, timestamp"):
        get_txn_author_agreement_handler.static_validation(request)

