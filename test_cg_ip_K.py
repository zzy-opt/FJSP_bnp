from instance_creator import create_fjsp_identical_machines
from fjspim_model import FJSPIMModel
from fjspim_model_c import FJSPIMModelC
from fjspim_problem import FJSPIMProblem
from fjsp2_cg_only import FJSPIMCG,SchedulePricer

if __name__ == '__main__':
	n_ops = [70] #
	#n_ops = [20,30]
	n_types = [3]
	n_low_machines = [4]
	#n_up_machines = 3
	n_precedence = [60]
	t_low = 10
	t_up = 30
	iterations = 10
	
	logname = "test_CG_K.csv"
	log_file = open(logname, "a")
	
	"""
	for a1 in n_ops:
		for a2 in n_types:
			for a3 in n_low_machines:
				a4 = a1
				log_file.write("size:{}_{}_{}_{}\n".format(a1,a2,a3,a4))
				for i in range(iterations):
					create_fjsp_identical_machines(a1,a2,a3,a3,t_low,t_up,a4,i+1)
					filename = str(a1)+"_" + str(a2)+"_" + str(a3)+"_" + str(a4)+"_" +str(i+1) +".fim"
					
					p = FJSPIMProblem(filename)
					m_ip = FJSPIMModel(p)
					m_ip.m.setParam('limits/time', 600)
					m_ip.m.optimize()
					status = m_ip.m.getStatus()
					#nodes = m_ip.getNodes()
					gap = m_ip.m.getGap()
					primal = m_ip.m.getPrimalbound()
					dual = m_ip.m.getDualbound()
					time = m_ip.m.getSolvingTime()
					if dual.is_integer():
						output_line = "{},{},{:d},{:d},{:.3f},{:.3f}\n".format(i+1,status,int(dual+0.001),int(primal+0.001),gap,time)
					else:
						output_line = "{},{},{:.2f},{:d},{:.3f},{:.3f}\n".format(i+1,status,dual,int(primal+0.001),gap,time)
					log_file.write(output_line)
	"""					
	for a1 in n_ops:
		for a2 in n_types:
			for a3 in n_low_machines:
				a4 = a1
				log_file.write("size:{}_{}_{}_{}\n".format(a1,a2,a3,a4))
				for i in range(iterations):
					filename = str(a1)+"_" + str(a2)+"_" + str(a3)+"_" + str(a4)+"_" +str(i+1) +".fim"
					#print(filename)
					p = FJSPIMProblem(filename)
					m_cg = FJSPIMCG(p)
					m_cg.m.setParam('limits/time', 600-m_cg.heu_time)
					m_cg.m.optimize()
					status = m_cg.m.getStatus()
					#nodes = m_ip.getNodes()
					primal = m_cg.m.getPrimalbound()
					#dual = m_cg.m.getDualbound()
					gap = m_cg.m.getGap()
					heu_time = m_cg.heu_time
					time = m_cg.m.getSolvingTime()
					output_line = "{},{},{:.2f},{:.3f},{:.3f},{:.3f}\n".format(i+1,status,primal,gap,heu_time,time)
					log_file.write(output_line)
				