# FJSP_bnp
Tackle flexible job shop with branch and price
The files start with "bnp" are implemented SCIP class for branch and price.
bnp_rmp.py is for the restricted master problem
bnp_pricer.py extend SCIP pricer to solve the subporblem
bnp_branch_conshdr_psi.py and bnp_branch_conshdr_lamda.py extend SCIP constraint handler to handle the branching decision
bnp_pricing_conshdr.py extend SCIP constraint handler to dynamically change the pricer data based on branching decision
fjspim_model.py contain the full IP model for orignal problem
fjspim_problem.py define the problem data structre
