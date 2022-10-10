from pyscipopt import Model, Pricer, Conshdlr, SCIP_RESULT, SCIP_PARAMSETTING, quicksum
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_pricer import SchedulePricer
from bnp_pricing_conshdr import PricingDataHdr
from bnp_constant import INTEGER_PRECISION

        
class BranchingConsHdrLamda(Conshdlr):

    def __init__(self,p,y,pattern_lamda_u_k, conshdr,pricer):
        print("initialize branching conshdr")
        self.p = p
        self.y = y
        self.pattern_lamda_u_k = pattern_lamda_u_k
        self.conshdr = conshdr
        self.pricer = pricer
        
        
        
    def conslock(self, constraint, locktype, nlockspos, nlocksneg):

        return {"result": SCIP_RESULT.SUCCESS}
    
    def consenforelax(self, solution, constraints, nusefulconss, solinfeasible):
        
        return {"result": SCIP_RESULT.FEASIBLE}
    
    def consenfops(self, constraints, nusefulconss, solinfeasible, objinfeasible):
        
        return{"result": SCIP_RESULT.SOLVELP}
    
    def conscheck(self, constraints, solution, checkintegrality, checklprows, printreason, completely):
        tuple_iuk = self.find_binary_lamda(solution)
 
        if len(tuple_iuk) == 1:
            print("find feasible lamda")
            return {"result": SCIP_RESULT.FEASIBLE}
        else:
            assert len(tuple_iuk) == 3
            return {"result": SCIP_RESULT.INFEASIBLE}


    def consenfolp(self, constraints, nusefulconss, solinfeasible):
        
        tuple_iuk = self.find_binary_lamda(None)
        if len(tuple_iuk) == 1:
            print("find feasible lamda")
            return {"result": SCIP_RESULT.FEASIBLE}
        assert(len(tuple_iuk) == 3)
        i = tuple_iuk[0]
        u = tuple_iuk[1]
        k = tuple_iuk[2]
        assert(i in self.p.M)
        assert(u in self.p.D[i])
        assert(k in self.p.K[i])
        
        
        if self.pricer.branch_feasibility_test("lamda",(i,u,k),0):
            print("branch on lamda_{}_{} on machine_{},value:{}".format(u,k,i,0))
            node_0 = self.model.createChild(0.0,self.model.getLocalEstimate())
            self.update_pricer((i,u,k),node_0,0)
            
        if self.pricer.branch_feasibility_test("lamda",(i,u,k),1):
            print("branch on lamda_{}_{} on machine_{},value:{}".format(u,k,i,1))
            node_1 = self.model.createChild(0.0,self.model.getLocalEstimate())
            self.update_pricer((i,u,k),node_1,1)
        #if True:
        
            
        #node_0 = self.model.createChild(0.0,self.model.getLocalEstimate())
        #self.update_pricer((i,u,k),node_0,0)
        
        
        #node_1 = self.model.createChild(0.0,self.model.getLocalEstimate())
        #self.update_pricer((i,u,k),node_1,1)
        #self.block_rmp_column((i,u,k),node_0,1)
        #self.block_rmp_column((i,u,k),node_1,0)
        
        
        

        return {"result": SCIP_RESULT.BRANCHED}

    def __isfractional(self,num):
        if -INTEGER_PRECISION < num and num < INTEGER_PRECISION:
            return False
        
        if 1-INTEGER_PRECISION < num and num < 1+INTEGER_PRECISION:
            return False
        
        return True      
        
    def find_binary_lamda(self,sol):
        # initialize all lamda_u_k to 0
        sum_lamda_u_k = {}
        for i in self.p.M:
            for u in self.p.D[i]:
                for k in self.p.K[i]:
                    sum_lamda_u_k[(u,k)] = 0
                    
        for i in self.p.M:
            assert(len(self.y[i])==len(self.pattern_lamda_u_k[i]))
            for j in range(len(self.y[i])):
                y_ij = self.model.getSolVal(sol, self.y[i][j])
                for pair in self.pattern_lamda_u_k[i][j]:
                    sum_lamda_u_k[pair] = sum_lamda_u_k[pair] + self.pattern_lamda_u_k[i][j][pair] * y_ij
                    
        for i in self.p.M:
            for u in self.p.D[i]:
                for k in self.p.K[i]:
                    if self.__isfractional(sum_lamda_u_k[(u,k)]):
                        #print("sum_lamda:{}".format(sum_lamda_u_k[(u,k)]))
                        #print((i,u,k))
                        return (i,u,k)
        return [0]
    
    # block columns which lamda_iuk is @value, 
    """
    def block_rmp_column(self,tuple_iuk,node,value):
        i = tuple_iuk[0]
        u = tuple_iuk[1]
        k = tuple_iuk[2]
        pair = (u,k)
        assert(len(self.y[i])==len(self.pattern_lamda_u_k[i]))
        blocked_columns = []
        for j in range(len(self.pattern_lamda_u_k[i])):
            #print("i:{},j:{},pair:{}".format(i,j,pair))
            if value == 0:
                if pair in self.pattern_lamda_u_k[i][j]:
                    if self.pattern_lamda_u_k[i][j][pair] == value:
                        blocked_columns.append(j)
                else:
                    blocked_columns.append(j)
            else: 
                assert(value == 1)
                if pair in self.pattern_lamda_u_k[i][j]:
                    if self.pattern_lamda_u_k[i][j][pair] == value:
                        blocked_columns.append(j)
        
        # try_to_add_cons_node
        # should i fix transformed or orginal variables
        
        #can not be done like this, the node where cons is added must be specified 
        #m.addCons(quicksum(self.y[i][j] for j in blocked_columns) == 0,
        #                                     name = "fix"+str(i)+"_"+str(u)+"_"+str(k), stickingatnode = True)    
        
        for j in blocked_columns:
            self.model.chgVarUbNode(node,self.y[i][j],0)
    """
    # update pricer to generate new column with lamda_iuk = @value
    def update_pricer(self,tuple_iuk,node,value):
        i = tuple_iuk[0]
        u = tuple_iuk[1]
        k = tuple_iuk[2]
        name = "lamda_"+str(u)+"_"+str(k)+"_"+str(value)
        cons = self.model.createCons(self.conshdr,name,stickingatnode=True)
        self.conshdr.createData(cons,i,"lamda",(u,k,value),node,self.pattern_lamda_u_k)
        self.model.addConsNode(node,cons)
        
        
        