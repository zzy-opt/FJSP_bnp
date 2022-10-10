from instance_creator import create_fjsp_identical_machines
from fjspim_model import FJSPIMModel
from fjspim_model_c import FJSPIMModelC
from fjspim_problem import FJSPIMProblem
from fjsp2_cg_only import FJSPIMCG,SchedulePricer


if __name__ == '__main__':
	n_ops = 12
	n_types = 2
	n_low_machines = 2
	n_up_machines = 3
	n_precedence = 25
	t_low = 5
	t_up = 10
	
	filename = str(n_ops)+"_" + str(n_types)+"_" + str(int(1/2*(n_low_machines+n_up_machines)))+"_" + str(n_precedence) +".fim"
	
	
	#create_fjsp_identical_machines(n_ops,n_types,n_low_machines,n_up_machines,t_low,t_up,n_precedence)
	
	filename = "20_3_4_60.fim"
	p = FJSPIMProblem(filename)
	#m = FJSPIMCG(p) 		#37	39	32	36  50
	#m = FJSPIMModelC(p)	#32	29	27
	m = FJSPIMModel(p)		#37	39	32	36	50
	#m.m.setObjective(1,sense = 'minimize')
	m.m.optimize()
	
	
	
	