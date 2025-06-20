import types
import flare_rpc

class DummyFunc:
    def __init__(self, result):
        self._result = result
    def call(self):
        return self._result

class DummyContract:
    def __init__(self, functions):
        self.functions = types.SimpleNamespace(**functions)

def test_list_providers():
    contract = DummyContract({'getProviders': lambda: DummyFunc(['0x1'])})
    w3 = types.SimpleNamespace(eth=types.SimpleNamespace(contract=lambda address, abi: contract))
    assert flare_rpc.list_providers(w3) == ['0x1']

def test_query_epoch_data():
    contract = DummyContract({'getEpochData': lambda eid: DummyFunc(('1','2','3'))})
    w3 = types.SimpleNamespace(eth=types.SimpleNamespace(contract=lambda address, abi: contract))
    assert flare_rpc.query_epoch_data(w3, 5) == ('1','2','3')

def test_delegation_logs():
    logs_called = {}
    def get_logs(params):
        logs_called['params'] = params
        return [1]
    w3 = types.SimpleNamespace(
        eth=types.SimpleNamespace(contract=lambda a,b: None, get_logs=get_logs),
        to_bytes=lambda hexstr: bytes.fromhex(hexstr[2:]),
        to_hex=lambda b: '0x'+b.hex()
    )
    addr = '0xabcdef0000000000000000000000000000000000'
    result = flare_rpc.delegation_logs(w3, 1, 2, provider=addr)
    assert result == [1]
    assert logs_called['params']['fromBlock'] == 1
    assert logs_called['params']['toBlock'] == 2

    assert logs_called['params']['topics'][0][0] == flare_rpc.DELEGATED_TOPIC
    assert logs_called['params']['topics'][0][1] == flare_rpc.UNDELEGATED_TOPIC


def test_get_all_delegation_logs():
    calls = []
    def get_logs(params):
        calls.append(params)
        return [params['fromBlock']]

    w3 = types.SimpleNamespace(
        eth=types.SimpleNamespace(
            contract=lambda a,b: None,
            get_logs=get_logs,
            block_number=210
        ),
        to_bytes=lambda hexstr: bytes.fromhex(hexstr[2:]),
        to_hex=lambda b: '0x'+b.hex()
    )

    result = flare_rpc.get_all_delegation_logs(w3, chunk_size=100)
    assert len(result) == 3
    assert calls[0]['fromBlock'] == 0
    assert calls[1]['fromBlock'] == 100
    assert calls[2]['toBlock'] == 210


