# Solving the Flexible Job Shop Problem with Sets of Identical Parallel Machines using Branch and Price
Master thesis project. In this project I used pySCIPOpt to implement Branch and Price and solve a special subset of the flexible job shop problem. 
Open access to the full text including detailed explaination about the mathematical formulation can be found at [Copenhagen University Library](https://soeg.kb.dk/permalink/45KBDK_KGL/1pioq0f/alma99124372362605763).

## About SCIP plugins implementation
I implemented two optinal SCIP plugins to guide the solver to work in a branch-and-price fashion. They are pricer and constraint handler. 
It is worth mentioning that the SCIP plugin 'branching rule' is not used here. In my formulation all integer variables are in the subproblem. The branching rule which is affiliated to the master problems cannot help branch on the integer varibles in the subproblem. Therefore constraint handler is used to branch here, it restricts master problem to generate column according to the branching decision.

* bnp_rmp.py is for the restricted master problem <br />
* bnp_pricer.py extend SCIP pricer to solve the subporblem <br />
* bnp_branch_conshdr_psi.py and bnp_branch_conshdr_lamda.py extend SCIP constraint handler to handle the branching decision <br />
* bnp_pricing_conshdr.py extend SCIP constraint handler to dynamically change the pricer data based on branching decision <br />
* fjspim_model.py contain the full IP model for orignal problem <br />
* fjspim_problem.py define the problem data structre <br />
