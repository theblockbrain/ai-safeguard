import os
import pyevmasm
from fastapi import FastAPI, Request, Form
from web3 import Web3
from utils import generate_cfg
from utils.infer_models import audit_contract
from utils.scrape_bytecode import scrape_bytecode
import logging
import coloredlogs
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.signatures_evm import get_signatures

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# create logger
logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger, fmt='[%(levelname)s]: %(message)s')

def validate_contract_address(contract_address):
    if not Web3.is_address(contract_address):
        error = 'Invalid contract address.'
        return False, error
    return True, None

def validate_rpc_url(rpc_url):
    if not rpc_url:
        error = 'RPC URL is required.'
        return False, error
    return True, None

@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/scrape_bytecode')
def scrape_bytecode_route(request: Request, contract_address: str = Form(...), rpc_url: str = Form(...)):
    try:
        # Validate input values
        valid_address, address_error = validate_contract_address(contract_address)
        if not valid_address:
            return templates.TemplateResponse("index.html", {"request": request, "error": address_error})

        valid_rpc, rpc_error = validate_rpc_url(rpc_url)
        if not valid_rpc:
            return templates.TemplateResponse("index.html", {"request": request, "error": rpc_error})

        scrape_bytecode(contract_address, rpc_url)
        bin_file = f'contracts/{contract_address}/{contract_address}.bin'
        if os.path.exists(bin_file):
            with open(bin_file) as f:
                output = f.read()
        return templates.TemplateResponse("index.html", {"request": request, "contract_address": contract_address, "output": output})

    except Exception as e:
        error = f"Error scraping bytecode: {e}"
        logger.error(error)
        return templates.TemplateResponse("index.html", {"request": request, "error": error})
    
@app.post('/generate_cfg')
def generate_cfg_route(request: Request, contract_address: str = Form(...), rpc_url: str = Form(...)):
    try:
        valid_address, address_error = validate_contract_address(contract_address)
        if not valid_address:
            return templates.TemplateResponse("index.html", {"request": request, "error": address_error})

        valid_rpc, rpc_error = validate_rpc_url(rpc_url)
        if not valid_rpc:
            return templates.TemplateResponse("index.html", {"request": request, "error": rpc_error})

        bin_file = f'contracts/{contract_address}/{contract_address}.bin'
        if not os.path.exists(bin_file):
            scrape_bytecode(contract_address, rpc_url)
            if not os.path.exists(bin_file):
                error = "Bytecode file does not exist."
                return templates.TemplateResponse("index.html", {"request": request, "error": error})

        generate_cfg.generate_control_flow_graph(bin_file, f"contracts/{contract_address}/{contract_address}.dot")

        dot_file = f'contracts/{contract_address}/{contract_address}.dot'
        if os.path.exists(dot_file):
            with open(dot_file) as f:
                output = f.read()

        return templates.TemplateResponse("index.html", {"request": request, "contract_address": contract_address, "output": output})

    except Exception as e:
        error = f"Error generating cfg: {e}"
        logger.error(error)
        return templates.TemplateResponse("index.html", {"request": request, "error": error})


@app.post('/disasm')
def disasm_route(request: Request, contract_address: str = Form(...), rpc_url: str = Form(...)):
    try:
        valid_address, address_error = validate_contract_address(contract_address)
        if not valid_address:
            return templates.TemplateResponse("index.html", {"request": request, "error": address_error})

        valid_rpc, rpc_error = validate_rpc_url(rpc_url)
        if not valid_rpc:
            return templates.TemplateResponse("index.html", {"request": request, "error": rpc_error})

        bin_file = f'contracts/{contract_address}/{contract_address}.bin'
        if not os.path.exists(bin_file):
            scrape_bytecode(contract_address, rpc_url)
            if not os.path.exists(bin_file):
                error = "Bytecode file does not exist."
                return templates.TemplateResponse("index.html", {"request": request, "error": error})

        with open(bin_file, mode="r") as file:
            evm_bytecode = file.read()
        disassembly = pyevmasm.evmasm.disassemble(evm_bytecode)
        asm_file = f"contracts/{contract_address}/{contract_address}.asm"
        with open(asm_file, mode="w") as file:
            file.write(disassembly)
        if os.path.exists(asm_file):
            with open(asm_file) as f:
                output = f.read()

        return templates.TemplateResponse("index.html", {"request": request, "contract_address": contract_address, "output": output})

    except Exception as e:
        error = f"Error generating disasm: {e}"
        logger.error(error)
        return templates.TemplateResponse("index.html", {"request": request, "error": error})


@app.post('/get_signatures')
def get_signatures_route(request: Request, contract_address: str = Form(...), rpc_url: str = Form(...)):
    try:
        valid_address, address_error = validate_contract_address(contract_address)
        if not valid_address:
            return templates.TemplateResponse("index.html", {"request": request, "error": address_error})

        valid_rpc, rpc_error = validate_rpc_url(rpc_url)
        if not valid_rpc:
            return templates.TemplateResponse("index.html", {"request": request, "error": rpc_error})

        bin_file = f'contracts/{contract_address}/{contract_address}.bin'
        if not os.path.exists(bin_file):
            scrape_bytecode(contract_address, rpc_url)
            if not os.path.exists(bin_file):
                error = "Bytecode file does not exist."
                return templates.TemplateResponse("index.html", {"request": request, "error": error})

        with open(bin_file, mode="r") as file:
            evm_bytecode = file.read()
        signatures = get_signatures(evm_bytecode)
        sigs_file = f"contracts/{contract_address}/{contract_address}.sigs"
        with open(sigs_file, mode="w") as file:
            for sig in signatures:
                formatted_sig = f"0x{sig[0]}: {sig[1]}"
                file.write(formatted_sig + "\n")
        if os.path.exists(sigs_file):
            with open(sigs_file) as f:
                output = f.read()

        return templates.TemplateResponse("index.html", {"request": request, "contract_address": contract_address, "output": output})

    except Exception as e:
        error = f"Error generating signatures: {e}"
        logger.error(error)
        return templates.TemplateResponse("index.html", {"request": request, "error": error})


@app.post('/audit_contract')
def audit_contract_route(request: Request, contract_address: str = Form(...), rpc_url: str = Form(...), token_type: str = Form(...)):
    try:
        valid_address, address_error = validate_contract_address(contract_address)
        if not valid_address:
            return templates.TemplateResponse("index.html", {"request": request, "error": address_error})

        valid_rpc, rpc_error = validate_rpc_url(rpc_url)
        if not valid_rpc:
            return templates.TemplateResponse("index.html", {"request": request, "error": rpc_error})

        dot_file = f'contracts/{contract_address}/{contract_address}.dot'
        if not os.path.exists(dot_file):
            bin_file = f'contracts/{contract_address}/{contract_address}.bin'
            if not os.path.exists(bin_file):
                scrape_bytecode(contract_address, rpc_url)
            if os.path.exists(bin_file):
                generate_cfg.generate_control_flow_graph(bin_file, dot_file)

        if os.path.exists(dot_file):
            result = audit_contract(dot_file, token_type)
            result = f"{result * 100:.2f}"
            if float(result) > 50:
                output = f"Result: {result}% ➡️ Contract is most likely malicious ⚠️🚫"
            else:
                output = f"Result: {result} ➡️ Contract is most likely non-malicious ✅"
        else:
            output = 'Control flow graph file does not exist.'

        return templates.TemplateResponse("index.html", {"request": request, "contract_address": contract_address, "output": output})

    except Exception as e:
        error = f"Error auditing contract: {e}"
        logger.error(error)
        return templates.TemplateResponse("index.html", {"request": request, "error": error})
