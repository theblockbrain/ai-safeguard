# AISafeGuard

This tool is designed to parse and analyze Ethereum Virtual Machine (EVM) bytecode. It supports scraping bytecode from the blockchain, generating a control flow graph (CFG) of the contract, disassembling the bytecode, extracting function signatures, and auditing the contract.

## Requirements

- Python 3
- pyevmasm
- web3
- graphviz
- coloredlogs

You can install the required libraries using pip:

```
pip install pyevmasm web3 graphviz coloredlogs
```

## Usage

To use the tool, run the following command:

```
python3 main.py <contract_address> [--rpc <node_url>] [--bytecode] [--cfg] [--disasm] [--sigs] [--audit] [--help]
```


- `<contract_address>` is the Ethereum address of the contract to parse.
- `--rpc <node_url>` is an optional parameter to specify the URL of an Ethereum node to use for scraping the bytecode. This parameter is required if you want to scrape the bytecode from the blockchain.
- `--bytecode` is an optional parameter to scrape the bytecode from the specified node.
- `--cfg` is an optional parameter to generate a control flow graph of the contract.
- `--disasm` is an optional parameter to disassemble the bytecode.
- `--sigs` is an optional parameter to extract function signatures.
- `--audit` is an optional parameter to audit the contract.
- `--help` is an optional parameter to show the help message.

## Examples

To scrape the bytecode from the blockchain and generate a CFG:

```
python3 main.py 0x1234567890abcdef --rpc https://mainnet.infura.io/v3/YOUR-ID --bytecode --cfg
```


## Note

This tool is a basic static analysis tool and will not be able to provide insights into dynamic behavior of a contract such as the the values stored in storage or memory during execution. Additionally, it may not be able to identify complex or obfuscated code structures that are designed to evade analysis. Therefore, it should be used as a supplement to other forms of analysis, such as dynamic analysis and manual code review, to obtain a comprehensive understanding of the contract's behavior.
