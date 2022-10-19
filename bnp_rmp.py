from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_PARAMSETTING, quicksum
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_pricer import SchedulePricer
from bnp_pricing_conshdr import PricingDataHdr
from bnp_branch_conshdr_lamda import BranchingConsHdrLamda
from bnp_branch_conshdr_psi import BranchingConsHdrPsi


class FJSPIMBNP:
    
    # return initial solution C
    # C is dic {i, C_i}
    # C_i is dic {u,t_u}, for u which I(u) = i, t_u > 0

    def find_init_sol(self,p:FJSPIMProblem):
        m = FJSPIMModel(p)
        #m.setEarlyTermination()
        m.m.setObjective(1,sense = 'minimize')
        m.m.optimize()
        sol = m.m.getBestSol()
        C_u = {}
        C_uk = {}
        lamda_uk = {}
        psi_uvk = {}
        for u in p.ops:
            C_u[u] = int(sol[m.C_u[u]]+0.001)
        for i in p.M:
            for k in p.K[i]:
                for u in p.D[i]:
                    if round(sol[m.lamda_u_k[(u,k)]]) == 1:
                        lamda_uk[(u,k)] = round(sol[m.lamda_u_k[(u,k)]])
                        C_uk[(u,k)] = round(sol[m.C_u_k[(u,k)]])
        for i in p.M:
            for k in p.K[i]:
                for pair in p.B[i]:
                    u = pair[0]
                    v = pair[1]
                    if round(sol[m.psi_u_v_k[(u,v,k)]]) == 1:
                        psi_uvk[(u,v,k)] = 1
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
        
        init_psi_uvk = {}
        self.init_psi_uvk = init_psi_uvk
        for i in p.M:
            psi_uvki = {}
            for pair in psi_uvki:
                if pair[0] in p.D[i]:
                    psi_uvki[pair] = psi_uvk[pair]
            init_psi_uvk[i] = psi_uvki
        return C
            
        
    def __init__(self,p:FJSPIMProblem):
        
        self.nodes = 0
        
        m = Model("fjspim_master")
        m.setIntParam("presolving/maxrounds", 0)
        m.setPresolve(SCIP_PARAMSETTING.OFF)
        m.setHeuristics(SCIP_PARAMSETTING.OFF)
        m.disablePropagation()
        self.m = m
        self.p = p
        # initial solution
        init_C = self.find_init_sol(p)
        
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
        
        # dummy cols for precedence constraints
        dummy_pre = {}
        for pair in p.A:
            dummy_pre[pair] = m.addVar("dummyPre_"+str(pair), vtype='C')
            
        # dummy cols for convexity constraints
        dummy_conv = {}
        for i in p.M:
            dummy_conv[i] = m.addVar("dummyConv_"+str(i), vtype='C')

            
        # initialize pattern
        pattern_C_u = {}
        pattern_C_u_k = {}
        pattern_lamda_u_k = {}
        pattern_psi_u_v_k = {}
        for i in p.M:
            C_ui = []
            C_uki = []
            lamda_uki = []
            psi_uvki = []
            C_ui.append(self.init_C[i])
            C_uki.append(self.init_C_uk[i])
            lamda_uki.append(self.init_lamda_uk[i])
            psi_uvki.append(self.init_psi_uvk[i])
            pattern_C_u[i] = C_ui
            pattern_C_u_k[i] = C_uki
            pattern_lamda_u_k[i] = lamda_uki
            pattern_psi_u_v_k[i] = psi_uvki
        self.pattern_C_u = pattern_C_u
        self.pattern_C_u_k = pattern_C_u_k
        self.pattern_lamda_u_k = pattern_lamda_u_k
        self.pattern_psi_u_v_k = pattern_psi_u_v_k
        
        # create the constraints
        # cons of the same type are stored in dict
        
        # cons 4.11 max_comp_u
        max_comp_u = {}
        for u in p.ops:
            max_comp_u[u] = m.addCons(C_max - self.y[p.I[u]][0] * init_C[p.I[u]][u]  >= 0 ,
                                      name = "max_comp_"+str(u), separate = False, modifiable = True)
        self.max_comp_u = max_comp_u
        
        
        
        # cons 4.12 precedence
        precedence_u_v = {}
        for pair in p.A:
            u = pair[0]
            v = pair[1]
            
            precedence_u_v[pair] = m.addCons(y[p.I[v]][0] * init_C[p.I[v]][v] - y[p.I[u]][0] * init_C[p.I[u]][u] + p.p[v] * dummy_pre[pair] >= p.p[v],
                                             name = "precedence_"+str(u)+"_"+str(v), separate = False, modifiable = True)
        self.precedence_u_v = precedence_u_v 
        
        # cons 4.13 convexity constraint
        convexity = {}
        for i in p.M:
            convexity[i] = m.addCons(y[i][0] + dummy_conv[i] == 1,name = "convexity_"+str(i), separate = False, modifiable = True)
        self.convexity = convexity
        
        # objective
        m.setObjective(C_max + quicksum(100*p.L * dummy_conv[i] for i in p.M) + quicksum(100*p.L * dummy_pre[pair] for pair in p.A),sense = 'minimize')
        
        # create pricer
        pricer = SchedulePricer()
        self.pricer = pricer
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
        pricer.data["pat_psi_u_v_k"] = pattern_psi_u_v_k

        # add initialization of fixed varibales list
        pricer.data["fixed_lamda"] = {}
        pricer.data["fixed_psi"]= {}
        for i in p.M:
            pricer.data["fixed_lamda"][i] = []
            pricer.data["fixed_psi"][i] = []
            
            
            
        # create pricing conshdr
        pricingConshdr = PricingDataHdr(pricer.data,self.y)
        m.includeConshdlr(pricingConshdr,"PricingConshdr","update pricer data after branching")
        self.pricingConshdr = pricingConshdr
        
        
        # create branching rules: assignment constraint and machine constraint
        brConshdrAssignment = BranchingConsHdrLamda(self.p,self.y,pattern_lamda_u_k,pricingConshdr,pricer)
        brConshdrMachine = BranchingConsHdrPsi(self.p,self.y,pattern_psi_u_v_k,pricingConshdr,pricer)
        m.includeConshdlr(brConshdrAssignment,"Assignment branching conshdlr","to branch lamda variables",chckpriority=100,needscons=False)
        m.includeConshdlr(brConshdrMachine,"Machine branching conshdlr","to branch psi variables",chckpriority=10,needscons=False)
        
    def get_nodes(self):
        return self.pricingConshdr.nodes
    
    def get_time_sub(self):
        return self.pricer.time_sub
    
    def get_sub_its(self):
        return self.pricer.sub_its
    def get_cols(self):
        len_y = 0
        for i in self.p.M:
            len_y = len_y + len(self.y[i])
        return len_y
    
        
        
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

        
            
if __name__ == '__main__':
    filename = "14_3_2_14_3.fim"
    p = FJSPIMProblem(filename)
    m = FJSPIMBNP(p)
    m.m.optimize()
    m.print_solution()
    m.m.writeProblem(filename+".lp",trans=True)

    