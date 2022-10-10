class FJSPIMProblem:
	def __init__(self,filename):
		f = open(filename, "r")
		# first line numbers
		l = f.readline().split(", ")
		l = list(map(int,l))
		n_ops = l[0]
		n_types= l[1]
		n_precedence = l[3]
		
		# second line operations
		l = f.readline().split(", ")
		l = list(map(int,l))
		ops = l
		
		# third line machine type per operation
		l = f.readline().split(", ")
		l = list(map(int,l))
		machine_types_per_op = l
		
		# forth line processing time per operation
		l = f.readline().split(", ")
		l = list(map(int,l))
		times = l
		
		# fifth line machine types
		l = f.readline().split(", ")
		l = list(map(int,l))
		machine_types = l
		
		# sixth line machine quantity per type of machine
		l = f.readline().split(", ")
		l = list(map(int,l))
		machine_quantities = l
		
		# seventh line precedence constraint[0]
		l = f.readline().split(", ")
		l = list(map(int,l))
		precedence_0 = l
		
		# eighth line precedence constraint[1]
		l = f.readline().split(", ")
		l = list(map(int,l))
		precedence_1 = l
		
		
		# number
		self.n_ops = n_ops
		self.n_types  = n_types
		self.n_precedence = n_precedence
		self.L = sum(times)

		
		# set
		# 'ops' list, operations set
		# 'A' list, precedence set, list of (u,v)
		# 'M' list, set of machine type i
		# 'D' dictionary of i and 'D_i'
		# 'B' dictionary of i and 'B_i'
		# 'K' dictionary of i and 'K_i'
		# 'I' dictionary of operation u and corresponding machine type i
		
		# 'ops' operations set
		self.ops = ops
		
		
		# 'I' dictionary of operation u and corresponding machine type i
		self.I = {}
		for j in range(len(ops)):
			u = ops[j]
			i = machine_types_per_op[j]
			self.I[u] = i
		
			
		
		# 'A' precedence set, list of (u,v)
		self.A = []
		for i in range(len(precedence_0)):
			pair = (precedence_0[i],precedence_1[i])
			self.A.append(pair)
			
		# 'M' set of machine type i
		self.M = list(range(1,n_types+1))
		
		
		# 'D' dictionary of i and 'D_i'
		# 'D_i' operations in same machine, list of operation u per machine i
		self.D = {}
		for i in self.M:
			D_i = []
			for j in range(len(machine_types_per_op)):
				if machine_types_per_op[j] == i:
					D_i.append(ops[j])
			self.D[i] = D_i
		
		# 'B' dictionary of i and 'B_i'
		# 'B_i' operation pair in the same machine
		self.B = {}
		for i in self.M:
			B_i = []
			D_i = self.D[i]
			for j_u in range(len(D_i)-1):
				for j_v in range(j_u+1,len(D_i)):
					pair = (D_i[j_u],D_i[j_v])
					B_i.append(pair)
			self.B[i] = B_i
		
		# 'K' dictionary of i and 'K_i'
		# 'K_i' machine set of the machine type 
		machine_quantities
		self.K = {}
		counter = 1
		for k in range(len(self.M)):
			K_i = []
			i = self.M[k]
			quantity = machine_quantities[k]
			for j in range(quantity):
				K_i.append(counter)
				counter = counter + 1
			self.K[i] = K_i
			
		# parameter
		# 'p' processing time, dictinary, p[i] = p_i  
		self.p = {}
		for i in range(len(self.ops)):
			u = self.ops[i]
			t = times[i]
			self.p[u] = t
		
		
		
if __name__ == '__main__':
	filename = "12_3_4_10.fim"
	p = FJSPIMProblem(filename)
			# set
		# 'ops' operations set
		# 'A' precedence set, list of (u,v)
		# 'M' set of machine type i
		# 'D' dictionary of i and 'D_i'
		# 'B' dictionary of i and 'B_i'
		# 'K' dictionary of i and 'K_i'
	print("----------------------------------ops----------------------------------")
	print(p.ops)
	print("----------------------------------A----------------------------------")
	print(p.A)
	print("----------------------------------M----------------------------------")
	print(p.M)
	print("----------------------------------D----------------------------------")
	print(p.D)
	print("----------------------------------B----------------------------------")
	print(p.B)
	print("----------------------------------K----------------------------------")
	print(p.K)
	print("----------------------------------p----------------------------------")
	print(p.p)
	print("----------------------------------L----------------------------------")
	print(p.L)
	