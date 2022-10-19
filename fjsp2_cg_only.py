from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_PARAMSETTING, quicksum, Eventhdlr, SCIP_EVENTTYPE
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_constant import PRICER_MAX_TIME, INTEGER_PRECISION
import time

class FJSPIMCG:
    
    # return initial solution C
    # C is dic {i, C_i}
    # C_i is dic {u,t_u}, for u which I(u) = i, t_u > 0
    
    
    
    def find_init_sol(self,p:FJSPIMProblem):
        m = FJSPIMModel(p)
        m.setEarlyTermination()
        m.m.optimize()
        sol = m.m.getBestSol()
        C_u = {}
        C_uk = {}
        lamda_uk = {}
        for u in p.ops:
            C_u[u] = int(sol[m.C_u[u]]+0.001)
        for i in p.M:
            for k in p.K[i]:
                for u in p.D[i]:
                    if round(sol[m.lamda_u_k[(u,k)]]) == 1:
                        lamda_uk[(u,k)] = round(sol[m.lamda_u_k[(u,k)]])
                        C_uk[(u,k)] = round(sol[m.C_u_k[(u,k)]])
        
        
        C = {}
        for i in p.M:
            C_i = {}
            for u in p.ops:
                if i == p.I[u]:
                    C_i[u] = C_u[u]
                else:
                    C_i[u] = 0
            C[i] = C_i
        m.print_solution()
        self.init_C = C
        
        init_C_uk = {}
        init_lamda_uk = {}
        
        for i in p.M:
            C_uki = {}
            lamda_uki = {}
            for pair in lamda_uk:
                if pair[0] in p.D[i]:
                    C_uki[pair] = C_uk[pair]
                    lamda_uki[pair] = lamda_uk[pair]
            init_C_uk[i] = C_uki
            init_lamda_uk[i] = lamda_uki
                
        self.init_C_uk = init_C_uk
        self.init_lamda_uk = init_lamda_uk
        
        return C
            
        
    def __init__(self,p:FJSPIMProblem):

        m = Model("fjspim_master")
        m.setPresolve(SCIP_PARAMSETTING.OFF)
        m.setHeuristics(SCIP_PARAMSETTING.OFF)
        m.disablePropagation()
        self.m = m
        self.p = p
        # initial solution
        heu_time_0 = time.time()
        init_C = self.find_init_sol(p)
        heu_time_1 = time.time()
        self.heu_time = heu_time_1 - heu_time_0
        
        # create the variables
        # C_max
        C_max = m.addVar("C_max")
        
        # create the variables y ={i:y_i} , y_i = []
        # convexity variables for each i in M
        # convexity variables index starts from 0, thus new variable index is len(y[i])
        y = {}
        for i in p.M:
            y_i = []
            y_i.append(m.addVar("y_"+str(i)+"_0",vtype='C'))
            y[i] = y_i
        self.y = y    
        
        
        pattern_C_u = {}
        pattern_C_u_k = {}
        pattern_lamda_u_k = {}
        for i in p.M:
            C_ui = []
            C_uki = []
            lamda_uki = []
            C_ui.append(self.init_C[i])
            C_uki.append(self.init_C_uk[i])
            lamda_uki.append(self.init_lamda_uk[i])
            pattern_C_u[i] = C_ui
            pattern_C_u_k[i] = C_uki
            pattern_lamda_u_k[i] = lamda_uki
        self.pattern_C_u = pattern_C_u
        self.pattern_C_u_k = pattern_C_u_k
        self.pattern_lamda_u_k = pattern_lamda_u_k
        
        
        # create the constraints
        # cons of the same type are stored in dict
        
        # cons 4.12 max_comp_u
        max_comp_u = {}
        for u in p.ops:
            max_comp_u[u] = m.addCons(C_max - self.y[p.I[u]][0] * init_C[p.I[u]][u]  >= 0 ,
                                      name = "max_comp_"+str(u), separate = False, modifiable = True)
        self.max_comp_u = max_comp_u
        
        # cons 4.13 precedence
        precedence_u_v = {}
        for pair in p.A:
            u = pair[0]
            v = pair[1]
            
            precedence_u_v[pair] = m.addCons(y[p.I[v]][0] * init_C[p.I[v]][v] - y[p.I[u]][0] * init_C[p.I[u]][u] >= p.p[v],
                                             name = "precedence_"+str(u)+"_"+str(v), separate = False, modifiable = True)
        self.precedence_u_v = precedence_u_v 
        
        # cons 4.14 convexity constraint
        convexity = {}
        for i in p.M:
            convexity[i] = m.addCons(y[i][0] == 1,name = "convexity_"+str(i), separate = False, modifiable = True)
        self.convexity = convexity
        
        # objective
        m.setObjective(C_max,sense = 'minimize')
        
        
        pricer = SchedulePricer()
        m.includePricer(pricer, "SchedulePricer", "Pricer to identify new schedule for every machine")
        pricer.data = {}
        #pricer.data[10] = "=============================1000000000000======================="
        # add constraints data to pricer
        pricer.data["comp_u"] = max_comp_u
        pricer.data["convex_i"] = convexity
        pricer.data["pre_u_v"] = precedence_u_v
        # add convexity variables data to pricer
        pricer.data["y"] = y
        # add problem parameter to pricer
        pricer.data["p"] = p
        pricer.data["pat_C_u"] = pattern_C_u
        pricer.data["pat_C_u_k"] = pattern_C_u_k
        pricer.data["pat_lamda_u_k"] = pattern_lamda_u_k
        
        
        
    def print_solution(self):
        """
        lendata = 0
        for pair in self.pattern_lamda_u_k:
            lendata = lendata+ len(self.pattern_lamda_u_k[pair])
        print("data len:{}".format(lendata))
        """
        sum_C_u = {}
        sum_C_u_k = {}
        sum_lamda_u_k = {}
        for i in self.p.M:
            for u in self.p.D[i]:
                sum_C_u[u] = 0
                for k in self.p.K[i]:
                    sum_C_u_k[(u,k)] = 0
                    sum_lamda_u_k[(u,k)] = 0
        
        for i in self.p.M:
            for j in range(len(self.y[i])):
                y_ij = self.m.getVal(self.y[i][j])
                for u in self.pattern_C_u[i][j]:
                    sum_C_u[u] = sum_C_u[u] + self.pattern_C_u[i][j][u] * y_ij
                for pair in self.pattern_C_u_k[i][j]:
                    sum_C_u_k[pair] = sum_C_u_k[pair] + self.pattern_C_u_k[i][j][pair] * y_ij
                    sum_lamda_u_k[pair] = sum_lamda_u_k[pair] + self.pattern_lamda_u_k[i][j][pair] * y_ij
                    
        
        for u in self.p.ops:
            print("C_{}:{}".format(u,sum_C_u[u]))
        for pair in sum_lamda_u_k:
            if sum_lamda_u_k[pair] != 0:
                print("lamda_{}_{}:{}".format(pair[0],pair[1],sum_lamda_u_k[pair]))
        for pair in sum_C_u_k:
            if sum_C_u_k[pair] != 0:
                print("C_{}_{}:{}".format(pair[0],pair[1],sum_C_u_k[pair]))
        
        
        
        
        
        
class SchedulePricer(Pricer):
    def __init__(self):
        self.cols = 0
        
    # The initialisation function for the variable pricer to retrieve the transformed constraints of the problem
    def pricerinit(self):
        #print(self.data[10])
        for u in self.data["p"].ops:
            self.data["comp_u"][u] = self.model.getTransformedCons(self.data["comp_u"][u])
        for i in self.data["p"].M:
            self.data["convex_i"][i] = self.model.getTransformedCons(self.data["convex_i"][i])
        for pair in self.data["p"].A:
            self.data["pre_u_v"][pair] = self.model.getTransformedCons(self.data["pre_u_v"][pair])
            
    def pricerredcost(self):        
        # get dual variables
        gamma_u={}
        alpha_u_v={}
        beta_i={}
        for u in self.data["p"].ops:
            gamma_u[u] = self.model.getDualsolLinear(self.data["comp_u"][u])
            #print("gamma_{}:{}".format(u,gamma_u[u]))
        for pair in self.data["p"].A:
            alpha_u_v[pair] = self.model.getDualsolLinear(self.data["pre_u_v"][pair])
            #print("alpha_{}_{}:{}".format(pair[0],pair[1],alpha_u_v[pair]))
        for i in self.data["p"].M:
            beta_i[i] = self.model.getDualsolLinear(self.data["convex_i"][i])
            #print("beta_{}:{}".format(i,beta_i[i]))
        
        # objctive coeff for each C_u
        c_coeff = {}
        for u in self.data["p"].ops:
            #print("---------------------------------------------------------")
            c_coeff[u] = gamma_u[u]
            #print("gamma_{}:{}".format(u,gamma_u[u]))
            for pair in self.data["p"].A:
                #print("alpha_{}_{}:{}".format(pair[0],pair[1],alpha_u_v[pair]))
                if u == pair[0]:
                    c_coeff[u] = c_coeff[u] + alpha_u_v[pair]
                if u == pair[1]:
                    c_coeff[u] = c_coeff[u] - alpha_u_v[pair]
            

        # calculate the column with least reduced cost for each sub-porblem
        for i in self.data["p"].M:
            #print("item:{}".format(i))
            m = Model("Schedule_sub_"+str(i))
            # Turning off presolve
            m.setPresolve(SCIP_PARAMSETTING.OFF)
            m.setHeuristics(SCIP_PARAMSETTING.OFF)
            
            # Setting the verbosity level to 0
            m.hideOutput()
            
            
            eventhdlr = EarlyTerminationEvent()
            m.includeEventhdlr(eventhdlr, "EarlyTerminationEvent", "python event handler to stop pricer early")
            
            # add subproblem variables
            # C_u
            C_u = {}
            for u in self.data["p"].D[i]:
                C_u[u] = m.addVar("C_"+str(u))
                
            # C_u_k, S_u_k and lamda_u_k
            C_u_k = {}
            S_u_k = {}
            lamda_u_k = {}
            for u in self.data["p"].D[i]:
                for k in self.data["p"].K[i]:
                    C_u_k[(u,k)] = m.addVar("C_"+str(u)+"_"+str(k))
                    S_u_k[(u,k)] = m.addVar("S_"+str(u)+"_"+str(k))
                    lamda_u_k[(u,k)] = m.addVar("lamda_"+str(u)+"_"+str(k),vtype='B')
                    
            # psi_u_v_k
            psi_u_v_k = {}
            for pair in self.data["p"].B[i]:
                u = pair[0]
                v = pair[1]
                for k in self.data["p"].K[i]:
                    psi_u_v_k[(u,v,k)] = m.addVar("psi_"+str(u)+"_"+str(v)+"_"+str(k),vtype='B')
            
            # add constraints
            
            # cons x.x machine constraints non-overlapping ,1&2
            for k in self.data["p"].K[i]:
                for pair in self.data["p"].B[i]:
                    u = pair[0]
                    v = pair[1]
                    m.addCons(C_u_k[(u,k)] - S_u_k[(v,k)] - self.data["p"].L * psi_u_v_k[(u,v,k)] <= 0)
                    m.addCons(C_u_k[(v,k)] - S_u_k[(u,k)] + self.data["p"].L * psi_u_v_k[(u,v,k)] <= self.data["p"].L)
        
            # cons x.x assignment constraint C_u = C_u_k when lamda_u_k = 1 ,1&2
            # cons x.x start time and end time
            for k in self.data["p"].K[i]:
                for u in self.data["p"].D[i]:
                    m.addCons(C_u[u] - C_u_k[(u,k)] - self.data["p"].L * lamda_u_k[(u,k)] >= -self.data["p"].L)
                    m.addCons(C_u[u] - C_u_k[(u,k)] + self.data["p"].L * lamda_u_k[(u,k)] <= self.data["p"].L)
                    m.addCons(S_u_k[(u,k)] - C_u_k[(u,k)] + self.data["p"].L * lamda_u_k[(u,k)] <= self.data["p"].L - self.data["p"].p[u]) 
            
            # cons x.x operation is only assigned once
            for u in self.data["p"].D[i]:
                m.addCons(quicksum(lamda_u_k[(u,k)] for k in self.data["p"].K[i]) == 1)
                m.addCons(C_u[u] <= self.data["p"].L)
            m.setObjective(quicksum(c_coeff[u] * C_u[u] for u in self.data["p"].D[i]) - beta_i[i],sense = 'minimize')
            m.optimize()
            
            #print(m.getStatus())
            
            redcost = m.getObjVal()
            """
            if m.getStatus == "optimal":
                redcost = m.getObjVal() - beta[i]
            else: 
                print("sub_problem is \"{}\"".format(m.getStatus()))
                
                print("coeffs")
                for u in self.data["p"].D[i]:
                    print("c_coeff_{}:{}".format(u,c_coeff[u]))
                
                redcost = 1
            """
            #print("redcost:{}".format(redcost))
            if redcost < -INTEGER_PRECISION:

                #for u in self.data["p"].D[i]:
                    #print("C_{}:{}".format(u,round(m.getVal(C_u[u]))))
                
                currentNumVar = len(self.data['y'][i])
                          
                # Creating new var; must set pricedVar to True
                newVar = self.model.addVar("y_"+str(i)+"_"+ str(currentNumVar), vtype = "C",obj = 0, pricedVar = True)
                # Adding the new variable to the constraints of the master problem
                
                # cons comp_u
                for u in self.data["p"].D[i]:
                    coeff = -1.0 * round(m.getVal(C_u[u]))
                    self.model.addConsCoeff(self.data["comp_u"][u], newVar, coeff)
                # cons pre_u_v
                for pair in self.data["p"].A:
                    u = pair[0]
                    v = pair[1]
                    if u in self.data["p"].D[i] and v in self.data["p"].D[i]:
                        coeff = round(m.getVal(C_u[v])) - round(m.getVal(C_u[u]))
                        self.model.addConsCoeff(self.data["pre_u_v"][pair], newVar, coeff)
                    elif u in self.data["p"].D[i]:
                        coeff =  -1.0 * round(m.getVal(C_u[u]))
                        self.model.addConsCoeff(self.data["pre_u_v"][pair], newVar, coeff)
                                              
                    elif v in self.data["p"].D[i]:
                        coeff =  round(m.getVal(C_u[v]))
                        self.model.addConsCoeff(self.data["pre_u_v"][pair], newVar, coeff)
                        
                # cons convex_i
                self.model.addConsCoeff(self.data["convex_i"][i], newVar, 1)
                
                self.data["y"][i].append(newVar)
                
                
                self.cols = self.cols+1
                print("add column,added cols:{}".format(self.cols))
                
                # add pattern back to master problem data
                pat_Cui = {}
                pat_Cuki = {}
                pat_lamda_uki = {}
                for pair in lamda_u_k:
                    if round(m.getVal(lamda_u_k[pair]))==1:
                        pat_Cuki[pair] = round(m.getVal(C_u_k[pair]))
                        pat_lamda_uki[pair] = round(m.getVal(lamda_u_k[pair]))
                for u in C_u:
                    pat_Cui[u] = round(m.getVal(C_u[u]))
                
                
                self.data["pat_C_u"][i].append(pat_Cui)
                self.data["pat_C_u_k"][i].append(pat_Cuki)
                self.data["pat_lamda_u_k"][i].append(pat_lamda_uki)
                    
        return {'result':SCIP_RESULT.SUCCESS}
        
class EarlyTerminationEvent(Eventhdlr):
    
    def eventinit(self):
        self.model.catchEvent(SCIP_EVENTTYPE.NODESOLVED, self)
        #self.model.catchEvent(SCIP_EVENTTYPE.BESTSOLFOUND, self)
    def eventexit(self):
        self.model.dropEvent(SCIP_EVENTTYPE.NODESOLVED, self)
        #self.model.catchEvent(SCIP_EVENTTYPE.BESTSOLFOUND, self)

    def eventexec(self, event):
        #print("BESTSOLFOUND")
        #print("time:{}".format(self.model.getSolvingTime() > PRICER_MAX_TIME))
        #print("model_name:{}".format(self.model.getProbName()))
        #print("oldBound:{},newBound:{}".format(event.getOldBound(),event.getNewBound()))
        if self.model.getSolvingTime() > PRICER_MAX_TIME:
            #print(event.getType())
            if self.model.getStage() == 9:
                objVal = self.model.getPrimalbound()
                dual = self.model.getDualbound()
                #print("sub_obj:{}".format(objVal))
                if objVal < -INTEGER_PRECISION or dual > INTEGER_PRECISION:
                    #print("interruptSolve")
                    self.model.interruptSolve()

        
        
        
if __name__ == '__main__':
    #1.90909090909091e+01 
    #2.70625000000000e+01
    #32
    #21
    filename = "70_3_4_70_9.fim"
    p = FJSPIMProblem(filename)
    m = FJSPIMCG(p)
    m.m.optimize()
    m.print_solution()
    
        