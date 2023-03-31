import os
import pyevmasm
from evm_parser import evm_cfg
from web3 import Web3
from utils import generate_cfg, visualization
from utils.infer_models import audit_contract
from utils.scrape_bytecode import scrape_bytecode
from utils.signatures_evm import get_signatures
import logging
import coloredlogs
from flask import Flask, request, render_template

app = Flask(__name__)

# create logger
logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger, fmt='[%(levelname)s]: %(message)s')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/parse', methods=['POST'])
def parse():
    contract_address = request.form['contract_address']
    rpc_url = request.form['rpc_url']
    bytecode = request.form.get('bytecode') is not None
    cfg = request.form.get('cfg') is not None
    disasm = request.form.get('disasm') is not None
    sigs = request.form.get('sigs') is not None
    audit = request.form.get('audit') is not None

    # validate the input values
    if not Web3.is_address(contract_address):
        return 'Invalid contract address.'

    if not rpc_url:
        return 'RPC URL is required.'

    output = {}

    if bytecode:
        scrape_bytecode(contract_address, rpc_url)
        with open(f'contracts/{contract_address}/{contract_address}.bin') as f:
            output['bytecode'] = f.read()

    if cfg:
        # check if the bytecode file exists
        if not os.path.exists(f"contracts/{contract_address}/{contract_address}.bin"):
            return "Bytecode file does not exist."
        generate_cfg.generate_control_flow_graph(f"contracts/{contract_address}/{contract_address}.bin",f"contracts/{contract_address}/{contract_address}.dot")

        with open(f'contracts/{contract_address}/{contract_address}.dot') as f:
            output['cfg'] = f.read()

    if disasm:
        # check if the bytecode file exists
        if not os.path.exists(f"contracts/{contract_address}/{contract_address}.bin"):
            return "Bytecode file does not exist."
        with open(f"contracts/{contract_address}/{contract_address}.bin", mode="r") as file:
            evm_bytecode = file.read()
        disassembly = pyevmasm.evmasm.disassemble(evm_bytecode)
        with open(f"contracts/{contract_address}/{contract_address}.asm", mode="w") as file:
            file.write(disassembly)
        with open(f'contracts/{contract_address}/{contract_address}.asm') as f:
            output['disasm'] = f.read()

    if sigs:
        # check if the bytecode file exists
        if not os.path.exists(f"contracts/{contract_address}/{contract_address}.bin"):
            return "Bytecode file does not exist."
        with open(f"contracts/{contract_address}/{contract_address}.bin", mode="r") as file:
            evm_bytecode = file.read()
        signatures = get_signatures(evm_bytecode)
        with open(f"contracts/{contract_address}/{contract_address}.sigs", mode="w") as file:
            for sig in signatures:
                file.write(sig + "\n")
        with open(f'contracts/{contract_address}/{contract_address}.sigs') as f:
            output['sigs'] = f.read()


    if audit:
        if os.path.exists(f"contracts/{contract_address}/{contract_address}.dot"):
            result = audit_contract(f"contracts/{contract_address}/{contract_address}.dot")
            result = f"{result * 100:.2f}"
            if float(result) > 50:
                output['audit'] = f"Result: {result}%<br>Contract is malicious<br>"
            else:
                output['audit'] = f"Result: {result}%<br>Contract is non-malicious<br>"
        else:
            output['audit'] = 'Control flow graph file does not exist.<br>'


    return render_template('index.html', contract_address=contract_address, output=output)



if __name__ == '__main__':
    app.run(debug=True)
