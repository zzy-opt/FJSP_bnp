from instance_creator import create_fjsp_identical_machines
from fjspim_model import FJSPIMModel
from fjspim_model_c import FJSPIMModelC
from fjspim_problem import FJSPIMProblem
from fjsp2_cg_only import FJSPIMCG,SchedulePricer


if __name__ == '__main__':
	n_ops = [20,40,70] #
	#n_ops = [20,30]
	n_types = [3]
	n_low_machines = [2]
	#n_up_machines = 3
	n_precedence = [60]
	t_low = 10
	t_up = 30
	iterations = 10
	
	logname = "LP_2_O.csv"
	log_file = open(logname, "a")
	
	
	for a1 in n_ops:
		for a2 in n_types:
			for a3 in n_low_machines:
				a4 = a1
				log_file.write("size:{}_{}_{}_{}\n".format(a1,a2,a3,a4))
				for i in range(iterations):
					#create_fjsp_identical_machines(a1,a2,a3,a3,t_low,t_up,a4,i+1)
					filename = str(a1)+"_" + str(a2)+"_" + str(a3)+"_" + str(a4)+"_" +str(i+1) +".fim"
					
					p = FJSPIMProblem(filename)
					m_lp = FJSPIMModelC(p)
					m_lp.m.setParam('limits/time', 600)
					m_lp.m.optimize()
					status = m_lp.m.getStatus()
					#nodes = m_ip.getNodes()
					gap = m_lp.m.getGap()
					primal = m_lp.m.getPrimalbound()
					dual = m_lp.m.getDualbound()
					time = m_lp.m.getSolvingTime()
					lamda = m_lp.getLamdas()
					psi = m_lp.getPsis()
					output_line = "{},{},{:.3f},{:d},{:d}\n".format(i+1,status,primal,lamda,psi)
					log_file.write(output_line)
				
	
	# 		#37	39	32	36  50
	#m = FJSPIMModelC(p)	#32	29	27
	#m = FJSPIMModel(p)		#37	39	32	36	50
	#m.m.setObjective(1,sense = 'minimize')
	#m.m.optimize()