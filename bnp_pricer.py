from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_PARAMSETTING, quicksum, Eventhdlr, SCIP_EVENTTYPE
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_constant import PRICER_MAX_TIME,INTEGER_PRECISION
import datetime

class SchedulePricer(Pricer):

    # The initialisation function for the variable pricer to retrieve the transformed constraints of the problem
    def pricerinit(self):
        #print(self.data[10])
        for u in self.data["p"].ops:
            self.data["comp_u"][u] = self.model.getTransformedCons(self.data["comp_u"][u])
        for i in self.data["p"].M:
            self.data["convex_i"][i] = self.model.getTransformedCons(self.data["convex_i"][i])
        for pair in self.data["p"].A:
            self.data["pre_u_v"][pair] = self.model.getTransformedCons(self.data["pre_u_v"][pair])
            
    
    def branch_feasibility_test(self,var_name,var_tuple,var_value):
        assert ((var_name == "lamda" and len(var_tuple)==3) or (var_name == "psi" and len(var_tuple)==4))
        assert (var_value == 0 or var_value == 1)
        
        
        i = var_tuple[0]
        
        
        m = Model("Schedule_sub_"+str(i))
        # Turning off presolve
        
        # Setting the verbosity level to 0
        m.hideOutput()
        
            
        # allow early termination if negative reduced cost it found 
        eventhdlr = EarlyTerminationEvent()
        m.includeEventhdlr(eventhdlr, "EarlyTerminationEvent", "python event handler to stop pricer early when negetive redeced cost is found")
            
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
            
        # cons x.x branching constraints which fix binary variables
        for x in self.data["fixed_lamda"][i]:
            #print("pricer - fixing lamda")
            u = x[0]
            assert(u in self.data["p"].D[i])
            k = x[1]
            assert(k in self.data["p"].K[i])
            value = x[2]
            assert(value == 1 or value == 0)
            if value == 1:
                m.chgVarLb(lamda_u_k[(u,k)],1)
            else:
                m.chgVarUb(lamda_u_k[(u,k)],0)
            #m.addCons(lamda_u_k[(u,k)] == value)
                
        for x in self.data["fixed_psi"][i]:
            #print("pricer - fixing psi")
            u = x[0]
            assert(u in self.data["p"].D[i])
            v = x[1]
            assert(v in self.data["p"].D[i])
            k = x[2]
            assert(k in self.data["p"].K[i])
            value = x[3]
            assert(value == 1 or value == 0)
            if value == 1:
                m.chgVarLb(psi_u_v_k[(u,v,k)],1)
            else:
                m.chgVarUb(psi_u_v_k[(u,v,k)],0)
                #m.addCons(psi_u_v_k[(u,v,k)] == value)
        
        if var_name == "lamda":
            u = var_tuple[1]
            k = var_tuple[2]
            if var_value == 1:
                m.chgVarLb(lamda_u_k[(u,k)],1)
            else:
                m.chgVarUb(lamda_u_k[(u,k)],0)
                
        if var_name == "psi":
            u = var_tuple[1]
            v = var_tuple[2]
            k = var_tuple[3]
            if var_value == 1:
                m.chgVarLb(psi_u_v_k[(u,v,k)],1)
            else:
                m.chgVarUb(psi_u_v_k[(u,v,k)],0)
        # objective
        m.setObjective(1,sense = 'minimize')
        m.optimize()
        
        if m.getStatus() == "infeasible":
            #print("infeasible,var:{},var_tuple:{},value:{}".format(var_name,var_tuple,var_value))
            return False
        
        return True
    
    
    def pricerredcost(self):  
        #print("try to find new cols")
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
            m = Model("Schedule_sub_"+str(i))
            # Turning off presolve
            m.setPresolve(SCIP_PARAMSETTING.OFF)
            # Setting the verbosity level to 0
            m.hideOutput()
            m.setHeuristics(SCIP_PARAMSETTING.OFF)
            
            # allow early termination if negative reduced cost it found 
            eventhdlr = EarlyTerminationEvent()
            m.includeEventhdlr(eventhdlr, "EarlyTerminationEvent", "python event handler to stop pricer early when negetive redeced cost is found")
            
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
            
            # cons x.x branching constraints which fix binary variables
            for x in self.data["fixed_lamda"][i]:
                #print("pricer - fixing lamda")
                u = x[0]
                assert(u in self.data["p"].D[i])
                k = x[1]
                assert(k in self.data["p"].K[i])
                value = x[2]
                assert(value == 1 or value == 0)
                if value == 1:
                    m.chgVarLb(lamda_u_k[(u,k)],1)
                else:
                    m.chgVarUb(lamda_u_k[(u,k)],0)
                #m.addCons(lamda_u_k[(u,k)] == value)
                
            for x in self.data["fixed_psi"][i]:
                #print("pricer - fixing psi")
                u = x[0]
                assert(u in self.data["p"].D[i])
                v = x[1]
                assert(v in self.data["p"].D[i])
                k = x[2]
                assert(k in self.data["p"].K[i])
                value = x[3]
                assert(value == 1 or value == 0)
                if value == 1:
                    m.chgVarLb(psi_u_v_k[(u,v,k)],1)
                else:
                    m.chgVarUb(psi_u_v_k[(u,v,k)],0)
                #m.addCons(psi_u_v_k[(u,v,k)] == value)
            
            
            
            # objective
            m.setObjective(quicksum(c_coeff[u] * C_u[u] for u in self.data["p"].D[i]) - beta_i[i],sense = 'minimize')
            m.optimize()
            #print(m.getStatus())
            
            assert(m.getStatus() != "infeasible")
            
                
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
            if redcost < -1e-08:

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
                
                
                #print("add column")
                
                # add pattern back to master problem data
                pat_Cui = {}
                pat_Cuki = {}
                pat_lamda_uki = {}
                pat_psi_uvki = {}
                for pair in lamda_u_k:
                    if round(m.getVal(lamda_u_k[pair]))==1:
                        pat_Cuki[pair] = round(m.getVal(C_u_k[pair]))
                        pat_lamda_uki[pair] = round(m.getVal(lamda_u_k[pair]))
                for u in C_u:
                    pat_Cui[u] = round(m.getVal(C_u[u]))
                for pair in psi_u_v_k:
                    if round(m.getVal(psi_u_v_k[pair]))==1:
                        pat_psi_uvki[pair] = 1
                
                self.data["pat_C_u"][i].append(pat_Cui)
                self.data["pat_C_u_k"][i].append(pat_Cuki)
                self.data["pat_lamda_u_k"][i].append(pat_lamda_uki)
                self.data["pat_psi_u_v_k"][i].append(pat_psi_uvki)
                
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
                objVal = self.model.getSolObjVal(None,original=True)
                if objVal < -1:
                    #print("interruptSolve")
                    self.model.interruptSolve()

        

    