# mongo-ai-money-transfer-prototype
Prototype for an AI-enhanced version of the MongoDB money transfer

This project demonstrates the fundamental building blocks of Temporal: 
Workflows and Activities, using the Temporal Python SDK. It simulates 
a money transfer between two bank accounts, demonstrating how to code
the business logic for both success and failure scenarios.

## Features

- **Workflow**: Orchestrates the money transfer process
- **Activities**: Handle withdrawal, deposit, and refund operations
- **Error Handling**: Demonstrates how to handle problems that occur
- **Saga Pattern**: Compensate with a refund if the deposit fails
- **Testing**: Comprehensive test suite for Workflows and Activities

## Prerequisites

- Python 3.8 or later
- Local Temporal Service

## Setup

1. **Start the Temporal Service** using the Temporal CLI:
   ```bash
   temporal server start-dev
   ```

2. **Clone and setup the project**:

   Open a new terminal window or tab, and then run the following 
   commands:

   ```bash
   git clone git@github.com:tomwheeler/mongo-ai-money-transfer-prototype.git
   cd money-transfer-project-template-python
   ```

3. **Create virtual environment and install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
   Repeat these two steps in a second terminal window or tab. 
   All of the commands that follow must be executed from within
   this virtual environment. Later, you will use one terminal session
   to run the Worker and the second to start the Workflow Execution.

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Run the Application

1. **Start the Worker** (in one terminal):
   ```bash
   python run_worker.py
   ```

2. **Start a Workflow** (in another terminal):
   ```bash
   python run_starter.py
   ```

   You can also specify custom parameters:
   ```bash
   python run_starter.py A123 B789 100 REF999
   ```

## Testing Different Scenarios

- **Normal Transfer**: Default parameters will complete successfully
- **Manager Approval**: Transferring $500 or more requires approval (use Signal to approve)
- **Insufficient Funds**: Use amount > $5000 to trigger insufficient funds error
- **Invalid Account**: Use target account "B5555" to trigger invalid account error (will refund)

## Layout

### Workflow Definition (`workflows.py`)
- **MoneyTransfer**: This Workflow orchestrates the transfer process.

### Activity Definition (`activities.py`)
- **BankingActivities.withdraw**: Withdraws money from source account
- **BankingActivities.deposit**: Deposits money to target account
- **BankingActivities.refund**: Refunds money back to source account (this
  is only invoked if the deposit failed)

### Shared code referenced in multiple files (`shared.py`)
- **PaymentDetails**: Data structure for transfer information
- **Custom Exceptions**: InvalidAccountError, InsufficientFundsError
- **Constants**: Task queue names and configuration

### Other code (the `utilities` subdirectory)
- The `list_workflows.py` file contains some functions for listing
  Workflow Executions, with variations that filter by whether they
  are currently running, have completed, or failed. 

## Monitoring
Open your browser to <http://localhost:8233> to access the Temporal
Web UI. You can use this to monitor Workflow Executions that are 
currently running as well as see the details of Workflow Executions
that have already completed.
