from pyscipopt import Model, Pricer, Conshdlr, SCIP_RESULT, SCIP_PARAMSETTING, quicksum
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_pricer import SchedulePricer
from bnp_pricing_conshdr import PricingDataHdr
from bnp_constant import INTEGER_PRECISION

        
class BranchingConsHdrPsi(Conshdlr):

    def __init__(self,p,y,pattern_psi_u_v_k, conshdr,pricer):
        self.p = p
        self.y = y
        self.pattern_psi_u_v_k = pattern_psi_u_v_k
        self.conshdr = conshdr
        self.pricer = pricer
          
    def conslock(self, constraint, locktype, nlockspos, nlocksneg):

        return {"result": SCIP_RESULT.SUCCESS}
    
    def consenforelax(self, solution, constraints, nusefulconss, solinfeasible):
        
        return {"result": SCIP_RESULT.FEASIBLE}
    
    def consenfops(self, constraints, nusefulconss, solinfeasible, objinfeasible):
        
        return{"result": SCIP_RESULT.SOLVELP}
    
    def conscheck(self, constraints, solution, checkintegrality, checklprows, printreason, completely):
        tuple_iuvk = self.find_binary_psi(solution)
        if len(tuple_iuvk) == 1:
            print("find feasible psi")
            return {"result": SCIP_RESULT.FEASIBLE}
        else:
            assert len(tuple_iuvk) == 3
            return {"result": SCIP_RESULT.INFEASIBLE}


    def consenfolp(self, constraints, nusefulconss, solinfeasible):
        
        tuple_iuvk = self.find_binary_psi(None)
        if len(tuple_iuvk) == 1:
            print("find feasible psi")
            return {"result": SCIP_RESULT.FEASIBLE}
        
        assert(len(tuple_iuvk) == 4)
        i = tuple_iuvk[0]
        u = tuple_iuvk[1]
        v = tuple_iuvk[2]
        k = tuple_iuvk[3]
        assert(i in self.p.M)
        assert((u,v) in self.p.B[i])
        assert(k in self.p.K[i])
        
        
        if self.pricer.branch_feasibility_test("psi",(i,u,v,k),0):
            #print("branch on psi:{},value:{}".format((i,u,v,k),0))
            node_0 = self.model.createChild(0.0,self.model.getLocalEstimate())
            self.update_pricer((i,u,v,k),node_0,0)
        
        
        if self.pricer.branch_feasibility_test("psi",(i,u,v,k),1):
            #print("branch on psi:{},value:{}".format((i,u,v,k),1))
            node_1 = self.model.createChild(0.0,self.model.getLocalEstimate())
            self.update_pricer((i,u,v,k),node_1,1)
            
        #node_0 = self.model.createChild(0.0,self.model.getLocalEstimate())
        #node_1 = self.model.createChild(0.0,self.model.getLocalEstimate())
        
        #self.block_rmp_column((i,u,v,k),node_0,1)
        #self.block_rmp_column((i,u,v,k),node_1,0)
        
        #self.update_pricer((i,u,v,k),node_0,0)
        #self.update_pricer((i,u,v,k),node_1,1)
        
        
        return {"result": SCIP_RESULT.BRANCHED}


    def __isfractional(self,num):
        if -INTEGER_PRECISION < num and num < INTEGER_PRECISION:
            return False
        
        if 1-INTEGER_PRECISION < num and num < 1+INTEGER_PRECISION:
            return False
        
        return True      
        
    def find_binary_psi(self,sol):
        # initialize all sum_psi_u_v_k to 0
        sum_psi_u_v_k = {}
        for i in self.p.M:
            for pair in self.p.B[i]:
                u = pair[0]
                v = pair[1]
                for k in self.p.K[i]:
                    sum_psi_u_v_k[(u,v,k)] = 0
                    
        for i in self.p.M:
            assert(len(self.y[i])==len(self.pattern_psi_u_v_k[i]))
            for j in range(len(self.y[i])):
                y_ij = self.model.getSolVal(sol, self.y[i][j])
                for pair in self.pattern_psi_u_v_k[i][j]:
                    sum_psi_u_v_k[pair] = sum_psi_u_v_k[pair] + self.pattern_psi_u_v_k[i][j][pair] * y_ij   
                    
        for i in self.p.M:
            for pair in self.p.B[i]:
                u = pair[0]
                v = pair[1]
                for k in self.p.K[i]:
                    if self.__isfractional(sum_psi_u_v_k[(u,v,k)]):
                        return (i,u,v,k)
        return [0]
    
    # block columns which psi_iuvk is @value, 
    """
    def block_rmp_column(self,tuple_iuvk,node,value):
        i = tuple_iuvk[0]
        u = tuple_iuvk[1]
        v = tuple_iuvk[2]
        k = tuple_iuvk[3]
        pair = (u,v,k)
        assert(len(self.y[i])==len(self.pattern_psi_u_v_k[i]))
        blocked_columns = []
        for j in range(len(self.pattern_psi_u_v_k[i])):
            if value == 0:
                if pair in self.pattern_psi_u_v_k[i][j]:
                    if self.pattern_psi_u_v_k[i][j][pair] == value:
                        blocked_columns.append(j)
                else:
                    blocked_columns.append(j)
            else: 
                assert(value == 1)
                if pair in self.pattern_psi_u_v_k[i][j]:
                    if self.pattern_psi_u_v_k[i][j][pair] == value:
                        print("block psi:{}".format(j))
                        blocked_columns.append(j)
       
        #cons_expr = quicksum(self.y[i][j] for j in blocked_columns) == 0
        #self.model.addLinearConsNode(cons_expr,node=node,stickingatnode=True)
        for j in blocked_columns:
            self.model.chgVarUbNode(node,self.y[i][j],0)
        
    """
    
    # update pricer to generate new column with psi_iuvk = @value
    def update_pricer(self,tuple_iuvk,node,value):
        i = tuple_iuvk[0]
        u = tuple_iuvk[1]
        v = tuple_iuvk[2]
        k = tuple_iuvk[3]
        name = "psi_"+str(u)+"_"+str(v)+"_"+str(k)+"_"+str(value)
        cons = self.model.createCons(self.conshdr,name,stickingatnode=True)
        self.conshdr.createData(cons,i,"psi",(u,v,k,value),node,self.pattern_psi_u_v_k)
        self.model.addConsNode(node,cons)
        
        
        
        