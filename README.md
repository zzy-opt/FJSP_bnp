# Solving the Flexible Job Shop Problem with Sets of Identical Parallel Machines using Branch and Price

## Overview
Master thesis project. In this project I used pySCIPOpt to implement Branch and Price and solve a special subset of the flexible job shop problem. 
Open access to the full text including detailed explanation about the mathematical formulation can be found at [Copenhagen University Library](https://soeg.kb.dk/permalink/45KBDK_KGL/1pioq0f/alma99124372362605763).

## Problem Description
The Flexible Job Shop Problem with Sets of Identical Parallel Machines (FJSIM) is an optimization problem that involves scheduling jobs on machines where:
- Each job consists of multiple operations that must be processed in a specific order
- Each operation can be processed on any machine from a specific set of identical parallel machines
- The goal is to minimize the makespan (total completion time)

## Implementation Details

### SCIP Plugins Implementation
I implemented two optional SCIP plugins to guide the solver to work in a branch-and-price fashion: pricer and constraint handler. 

It is worth mentioning that the SCIP plugin 'branching rule' is not used here. In my formulation all integer variables are in the subproblem. The branching rule which is affiliated to the master problems cannot help branch on the integer variables in the subproblem. Therefore constraint handler is used to branch here, it restricts master problem to generate column according to the branching decision.

### File Structure
- `bnp_rmp.py` - Implementation of the restricted master problem
- `bnp_pricer.py` - Extension of SCIP pricer to solve the subproblem
- `bnp_branch_conshdr_psi.py` and `bnp_branch_conshdr_lamda.py` - Extensions of SCIP constraint handlers to handle the branching decision
- `bnp_pricing_conshdr.py` - Extension of SCIP constraint handler to dynamically change the pricer data based on branching decision
- `bnp_constant.py` - Constants and parameters used across the project
- `fjspim_model.py` - Contains the full IP model for the original problem
- `fjspim_model_c.py` - Alternative implementation of the FJSIM model
- `fjspim_problem.py` - Defines the problem data structure
- `fjspim_main.py` - Main execution script for the FJSIM solver
- `instance_creator.py` - Utility for creating problem instances
- `problem_instances/` - Directory containing problem instance files in .fim format
- Test files: `test_*.py` - Various test scripts for different components

### Problem Instances
The `problem_instances/` directory contains various test instances in .fim format with different configurations:
- Different numbers of jobs, machines, and operations
- Various problem sizes from small (10x2) to large (70x5) instances
- Multiple test cases for each configuration (1-10)

## Usage
To run the branch-and-price algorithm:
```bash
python fjspim_main.py
```

Various test scripts are available to test different components of the implementation.

## Dependencies
- Python 3.x
- pyscipopt (pySCIPOpt)
- numpy (if used in the implementation)

## Methodology
The branch-and-price approach combines:
1. Column generation in the master problem to handle the exponential number of variables
2. Branching decisions handled through constraint handlers
3. Pricing subproblems solved with custom pricers to generate new columns

## License
[Specify license type if applicable]
