from fjspim_problem import FJSPIMProblem
from pyscipopt import Model,quicksum


class FJSPIMModelC:
	def __init__(self,p:FJSPIMProblem):
		m = Model("fjspim")
		self.lamda_count = 0
		self.psi_count = 0
		self.m = m
		self.p = p
		
		# create the variables
		# variables of the same type are stored in dict
		
		# C_max
		C_max = m.addVar("C_max")
		
		# C_u
		C_u = {}
		for u in p.ops:
			C_u[u] = m.addVar("C_"+str(u))	
		self.C_u = C_u
		
		# C_u_k
		C_u_k = {}
		for u in p.ops:
			for i in p.M:
				D_i = p.D[i]
				if u in D_i:
					for k in p.K[i]:
						C_u_k[(u,k)] = m.addVar("C_"+str(u)+"_"+str(k))						
		self.C_u_k = C_u_k
		
		
		# S_u_k
		S_u_k = {}
		for u in p.ops:
			for i in p.M:
				D_i = p.D[i]
				if u in D_i:
					for k in p.K[i]:
						S_u_k[(u,k)] = m.addVar("S_"+str(u)+"_"+str(k))
		# lamda_u_k
		lamda_u_k = {}
		for u in p.ops:
			for i in p.M:
				D_i = p.D[i]
				if u in D_i:
					for k in p.K[i]:
						lamda_u_k[(u,k)] = m.addVar("lamda_"+str(u)+"_"+str(k),vtype='C')
						self.lamda_count = self.lamda_count + 1
		self.lamda_u_k = lamda_u_k
		# psi_u_k
		psi_u_v_k = {}
		for i in p.M:
			for pair in p.B[i]:
				u = pair[0]
				v = pair[1]
				for k in p.K[i]:
					psi_u_v_k[(u,v,k)] = m.addVar("psi_"+str(u)+"_"+str(v)+"_"+str(k),vtype='C')
					self.psi_count = self.psi_count + 1
		
		# create the constraints
		# cons of the same type are stored in dict
		
		# cons 4.2 max_comp_u
		max_comp_u = {}
		for u in p.ops:
			max_comp_u[u] = m.addCons(C_max >= C_u[u],name = "max_comp_"+str(u))
		
		# cons 4.3 precedence
		precedence_u_v = {}
		for pair in p.A:
			u = pair[0]
			v = pair[1]
			#print("C_{} <= C_{} - {}".format(u,v,p.p[v]))
			precedence_u_v[pair] = m.addCons(C_u[u] <= C_u[v] - p.p[v],name = "precedence_"+str(u)+"_"+str(v))
		
		# cons 4.4 bounds 
		# no bounds yet
		
		# cons 4.5 machine non-overlap part1
		machine_overlap_1_u_v_k_i = {}
		for i in p.M:
			for k in p.K[i]:
				for pair in p.B[i]:
					u = pair[0]
					v = pair[1]
					machine_overlap_1_u_v_k_i[(u,v,k,i)] = m.addCons(C_u_k[(u,k)] <= S_u_k[(v,k)] + p.L * psi_u_v_k[(u,v,k)] ,
																		 name = "preceden_"+str(u)+"_"+str(v)+"_"+str(k))
		# cons 4.6 machine non-overlap part2
		machine_overlap_2_u_v_k_i = {}
		for i in p.M:
			for k in p.K[i]:
				for pair in p.B[i]:
					u = pair[0]
					v = pair[1]
					machine_overlap_2_u_v_k_i[(u,v,k,i)] = m.addCons(C_u_k[(v,k)] <= S_u_k[(u,k)] + p.L - p.L * psi_u_v_k[(u,v,k)] ,
																		 name = "preceden_"+str(u)+"_"+str(v)+"_"+str(k))
		
		# cons 4.7 operation real completion time
		comp_time_u_k = {}
		for i in p.M:
			for u in p.D[i]:
				for k in p.K[i]:
					comp_time_u_k[(u,k)] = m.addCons(C_u[u] >= C_u_k[(u,k)] - p.L + p.L * lamda_u_k[(u,k)],
														name = "comp_time_"+str(u)+"_"+str(k))
		### comment needs to be upadted			
		# cons 4.7 operation real completion time_part2
		
		comp_time_2_u_k = {}
		for i in p.M:
			for u in p.D[i]:
				for k in p.K[i]:
					comp_time_2_u_k[(u,k)] = m.addCons(C_u[u] - p.L + p.L * lamda_u_k[(u,k)] <= C_u_k[(u,k)] ,
													name = "comp_time_2_"+str(u)+"_"+str(k))
		
		# cons 4.9 operation comp time and start time per machine
		start_time_u_k = {}
		for i in p.M:
			for u in p.D[i]:
				for k in p.K[i]:
					start_time_u_k[(u,k)] = m.addCons(S_u_k[(u,k)] <= C_u_k[(u,k)] - p.p[u] + p.L - p.L * lamda_u_k[(u,k)],
														name = "start_time_"+str(u)+"_"+str(k))
		"""			
		# cons 4.10 set time of unselected machines to 0
		unselected_machine_u_k = {}
		for i in p.M:
			for u in p.D[i]:
				for k in p.K[i]:
					unselected_machine_u_k[(u,k)] = m.addCons(S_u_k[(u,k)] + C_u_k[(u,k)] <= p.L * lamda_u_k[(u,k)],
																  name = "unselected_machine_"+str(u)+"_"+str(k))
		"""	
		# cons 4.11 operations are only assigned once
		assigned_once_u = {}
		for i in p.M:
			for u in p.D[i]:
				assigned_once_u[u] = m.addCons(quicksum(lamda_u_k[(u,k)] for k in p.K[i]) == 1,
																  name = "unselected_machine_"+str(u))

		# objective
		m.setObjective(C_max,sense = 'minimize')
		#m.setObjective(1,sense = 'minimize')
		
	def print_solution(self):
		C_u_k = self.C_u_k
		p = self.p
		m = self.m
		C_u = self.C_u
		lamda_u_k = self.lamda_u_k
		
		sol = m.getBestSol()
		
		for i in p.M:
			for u in p.D[i]:
				for k in p.K[i]:
					if int(sol[lamda_u_k[(u,k)]]+0.001) != 0:
						print("C_{}_{}: {}".format(u,k,int(sol[C_u_k[(u,k)]]+0.001)))
		
		for u in p.ops:
			print("C_{}: {}".format(u,int(sol[C_u[u]]+0.001)))
		
	def check_feasibility(self):
		
		sol = self.m.getBestSol()
		# 1 check assignment, C_u_k = C_u if lambda_u_k is 1
		print("----------check assignment----------")
		for u in self.p.ops:
			for i in self.p.M:
				for k in self.p.K[i]:
					if u in p.D[i]:
						if int(round(sol[self.lamda_u_k[(u,k)]])) == 1:
							if round(sol[self.C_u_k[(u,k)]]) != round(sol[self.C_u[u]]):
								print("assignment error: C_{}_{}".format(u,k))
								return 0
		print("----------pass assignment check----------")
		
		# 2 check precedence constraints
		print("----------check precedence----------")
		for pair in self.p.A:
			u = pair[0]
			v = pair[1]
			C_u = round(sol[self.C_u[u]])
			C_v = round(sol[self.C_u[v]])
			if C_u > C_v - self.p.p[v]:
				print("precedence error, job:{} and job:{}, of which completion time are {} and {}".format(u,v,C_u,C_v))
				return 0
		print("----------pass precedence check----------")
		# 3 check machine constraint
		print("----------check machine----------")
		for i in self.p.M:
			for k in self.p.K[i]:
				ops_k = []
				for u in self.p.D[i]:
					if int(round(sol[self.lamda_u_k[(u,k)]])) == 1:
						ops_k.append(u)
				for u in ops_k:
					for v in ops_k:
						if u != v:
							C_u = round(sol[self.C_u[u]])
							C_v = round(sol[self.C_u[v]])
							ubeforev = (C_v - self.p.p[v]) - C_u
							uafterv = (C_u - self.p.p[u]) - C_v
							if ubeforev < 0 and uafterv < 0:
								print("machine constraints error, job:{} and job:{}, of which completion time are {} and {}".format(u,v,C_u,C_v))
								return 0
		print("----------pass machine check----------")
	

	def getLamdas(self):
		return self.lamda_count
	def getPsis(self):
		return self.psi_count
		
if __name__ == '__main__':
	filename = "150_10_2_300.fim"
	p = FJSPIMProblem(filename)
	m = FJSPIMModelC(p)
	m.m.optimize()