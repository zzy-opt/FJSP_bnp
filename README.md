# FJSP_bnp
Tackle flexible job shop with branch and price <br />
The files start with "bnp" are implemented SCIP class for branch and price. <br />
bnp_rmp.py is for the restricted master problem <br />
bnp_pricer.py extend SCIP pricer to solve the subporblem <br />
bnp_branch_conshdr_psi.py and bnp_branch_conshdr_lamda.py extend SCIP constraint handler to handle the branching decision <br />
bnp_pricing_conshdr.py extend SCIP constraint handler to dynamically change the pricer data based on branching decision <br />
fjspim_model.py contain the full IP model for orignal problem <br />
fjspim_problem.py define the problem data structre <br />
