import random

def create_fjsp_identical_machines(n_ops,n_types,n_low_machines,n_up_machines,t_low,t_up,n_precedence):
	filename = str(n_ops)+"_" + str(n_types)+"_" + str(int(1/2*(n_low_machines+n_up_machines)))+"_" + str(n_precedence) +".fim"
	f = open(filename, "w")
	f.write(str(n_ops)+", " + str(n_types)+", " + str(int(1/2*(n_low_machines+n_up_machines)))+", " + str(n_precedence)+"\n")
	# operations
	for i in range(1,n_ops):
		f.write(str(i)+", ")
	f.write(str(n_ops)+"\n")
	# machine type for each operation
	for i in range(1, n_ops+1):
		if i < n_types:
			f.write(str(i)+", ")
		elif i != n_ops:
			f.write(str(int(random.random()*n_types+1))+", ")
		else:
			f.write(str(int(random.random()*n_types+1))+"\n")
	# processing time for each operation
	for i in range(1, n_ops+1):
		if i != n_ops:
			f.write(str(int(random.random()*(t_up+1-t_low)+t_low))+", ")
		else:
			f.write(str(int(random.random()*(t_up+1-t_low)+t_low))+"\n")
			
	# machine types
	for i in range(1,n_types):
		f.write(str(i)+", ")
	f.write(str(n_types)+"\n")
	# number of machines per type 
	for i in range(1, n_types+1):
		if i != n_types:
			f.write(str(int(random.random()*(n_up_machines+1-n_low_machines)+n_low_machines))+", ")
		else:
			f.write(str(int(random.random()*(n_up_machines+1-n_low_machines)+n_low_machines))+"\n")

	# precedence constraint
	k = 0
	precedence = []
	while k < n_precedence:
		i = int(random.random()*(n_ops-1)+1)
		j = int(random.random() * (n_ops + 1 - i-1) + i+1)
		pair = (i,j)
		
		if pair not in precedence:
			precedence.append(pair)
			print(pair)
			k = k+1
	for i in range(n_precedence):
		if i != n_precedence-1:
			f.write(str(precedence[i][0])+", ")
		else:
			f.write(str(precedence[i][0])+"\n")
	for i in range(n_precedence):
		if i != n_precedence-1:
			f.write(str(precedence[i][1])+", ")
		else:
			f.write(str(precedence[i][1])+"\n")		
	
	f.close()
	
	
if __name__ == '__main__':
	n_ops = 100
	n_types = 7
	n_low_machines = 4
	n_up_machines = 4
	n_precedence = 150
	t_low = 10
	t_up = 20
	create_fjsp_identical_machines(n_ops,n_types,n_low_machines,n_up_machines,t_low,t_up,n_precedence)
