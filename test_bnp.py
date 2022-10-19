from instance_creator import create_fjsp_identical_machines
from fjspim_model import FJSPIMModel
from fjspim_model_c import FJSPIMModelC
from fjspim_problem import FJSPIMProblem
from bnp_rmp import FJSPIMBNP

if __name__ == '__main__':
	n_ops = [10,15,20] #
	#n_ops = [20,30]
	n_types = [3]
	n_low_machines = [2]
	#n_up_machines = 3
	#n_precedence = [10]
	t_low = 10
	t_up = 30
	iterations = range(10)
	
	logname = "test_bnp.csv"
	log_file = open(logname, "a")
	
	"""
	for a1 in n_ops:
		for a2 in n_types:
			for a3 in n_low_machines:
				a4 = a1
				log_file.write("size:{}_{}_{}_{}\n".format(a1,a2,a3,a4))
				for i in iterations:
					#create_fjsp_identical_machines(a1,a2,a3,a3,t_low,t_up,a4,i+1)
					filename = str(a1)+"_" + str(a2)+"_" + str(a3)+"_" + str(a4)+"_" +str(i+1) +".fim"
					
					p = FJSPIMProblem(filename)
					m_bnp = FJSPIMBNP(p)
					m_bnp.m.setParam('limits/time', 600)	
					m_bnp.m.optimize()
					status = m_bnp.m.getStatus()
					gap = m_bnp.m.getGap()
					primal = m_bnp.m.getPrimalbound()
					dual = m_bnp.m.getDualbound()
					time = m_bnp.m.getSolvingTime()
					
					nodes = m_bnp.m.getNNodes()
					time_sub = m_bnp.get_time_sub()
					its_sub = m_bnp.get_sub_its()
					cols = m_bnp.get_cols()
					
			
					output_line = "{},{},{:.2f},{:d},{:.3f},{:d},{:d},{:d},{:.3f},{:.3f}\n".format(i+1,status,dual,int(primal+0.001),gap,cols,nodes,its_sub,time_sub,time)
					log_file.write(output_line)
	"""			
	for a1 in n_ops:
		for a2 in n_types:
			for a3 in n_low_machines:
				a4 = a1
				log_file.write("size:{}_{}_{}_{}\n".format(a1,a2,a3,a4))
				for i in iterations:
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
					nodes = m_ip.m.getNNodes()
					if dual.is_integer():
						output_line = "{},{},{:d},{:d},{:d},{:.3f},{:.3f}\n".format(i+1,status,nodes,int(dual+0.001),int(primal+0.001),gap,time)
					else:
						output_line = "{},{},{:d},{:.2f},{:d},{:.3f},{:.3f}\n".format(i+1,status,nodes,dual,int(primal+0.001),gap,time)
					log_file.write(output_line)
		
	for a1 in n_ops:
		for a2 in n_types:
			for a3 in n_low_machines:
				a4 = a1
				log_file.write("size:{}_{}_{}_{}\n".format(a1,a2,a3,a4))
				for i in iterations:
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