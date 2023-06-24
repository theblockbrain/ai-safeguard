# AI-SafeGuard FastAPI

This tool is a FastAPI application that is designed to help analyze Ethereum smart contracts. It is capable of several tasks such as scraping bytecode, generating control flow graphs, disassembling code, extracting function signatures, and auditing contracts.

## Features

- **Scrape Bytecode:** Scrapes the bytecode of the contract using its address and the provided RPC URL.
- **Generate Control Flow Graphs:** Generate a control flow graph of the contract's bytecode.
- **Disassemble Code:** Disassemble the contract's bytecode.
- **Extract Function Signatures:** Extract the function signatures from the contract's bytecode.
- **Audit Contract:** Audit the contract using its control flow graph and a specified token type.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

This project requires the following libraries: 

- FastAPI
- Web3
- pyevmasm
- Jinja2Templates
- coloredlogs

### Installing

To get started, clone the repo and install the dependencies:

```bash
git clone https://github.com/yourusername/ethereum-contract-analyzer.git
cd ethereum-contract-analyzer
pip install -r requirements.txt
```

### Running

To run the application, use the following command:

```bash
uvicorn main:app --reload
```

The application will be available at http://

## Documentation

The documentation for this project is available at /docs.

# Contributing

We welcome contributions to this project. Please feel free to open a pull request or an issue on the GitHub page.


# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Authors

- **[Nader Bennour](www.linkedin.com/in/naderfyi)** - *Initial work*

## Note

This tool is a basic static analysis tool and will not be able to provide insights into dynamic behavior of a contract such as the the values stored in storage or memory during execution. 

Additionally, it may not be able to identify complex or obfuscated code structures that are designed to evade analysis. Therefore, it should be used as a supplement to other forms of analysis, such as dynamic analysis and manual code review, to obtain a comprehensive understanding of the contract's behavior.
