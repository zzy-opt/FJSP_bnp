from pyscipopt import Model, Pricer,Branchrule, SCIP_RESULT, SCIP_PARAMSETTING, quicksum
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_pricer import SchedulePricer
from bnp_constant import INTEGER_PRECISION
from bnp_conshdr import PricingDataHdr


class BranchingMachine(Branchrule):

    def __init__(self,p,y,pattern_psi_u_v_k, conshdr):
        self.p = p
        self.y = y
        self.pattern_psi_u_v_k = pattern_psi_u_v_k
        self.conshdr = conshdr
        
            
    def branchinitsol(self):
        self.y_trans = {}
        for i in self.p.M:
            y_trans_i = []
            y_i = self.y[i]
            for y_var in y_i:
                y_trans_i.append(self.model.getTransformedVar(y_var))
            self.y_trans[i] = y_trans_i
    
    @staticmethod
    def __isfractional(num):
        if -INTEGER_PRECISION < num and num < INTEGER_PRECISION:
            return False
        
        if 1-INTEGER_PRECISION < num and num < 1+INTEGER_PRECISION:
            return False
        
        return True
    
    
    def find_binary_psi(self):
        # initialize all sum_psi_u_v_k to 0
        sum_psi_u_v_k = {}
        for i in self.p.M:
            for pair in self.p.B[i]:
                u = pair[0]
                v = pair[1]
                for k in self.p.K[i]:
                    sum_psi_u_v_k[(u,v,k)] = 0                    
                    
        for i in self.p.M:
            # not sure about y_trans since some cols are automatically removed
            assert(len(self.y_trans[i])==len(self.pattern_psi_u_v_k[i]))
            for j in range(len(self.y_trans[i])):
                y_ij = self.y_trans[i][j].getLPSol()
                for pair in self.pattern_psi_u_v_k[i][j]:
                    sum_psi_u_v_k[pair] = sum_psi_u_v_k[pair] + self.pattern_psi_u_v_k[i][j][pair] * y_ij
                    
        for i in self.p.M:
            for pair in self.p.B[i]:
                u = pair[0]
                v = pair[1]
                for k in self.p.K[i]:
                    if __isfractional(sum_psi_u_v_k[(u,v,k)]):
                        return (i,u,v,k)
        return 0
    
    
    def branch(self):
        tuple_iuvk = find_binary_psi()
        if len(tuple_iuvk) == 1:
            return {"result": SCIP_RESULT.DIDNOTRUN}
        assert(len(tuple_iuvk) == 4)
        i = tuple_iuvk[0]
        u = tuple_iuvk[1]
        v = tuple_iuvk[2]
        k = tuple_iuvk[3]
        assert(i in self.p.M)
        assert((u,v) in self.p.B[i])
        assert(k in self.p.K[i])
        
        node_0 = self.model.createChild(0.0,self.model.getLocalEstimate())
        node_1 = self.model.createChild(0.0,self.model.getLocalEstimate())
        
        self.block_rmp_column((i,u,v,k),node_0,1)
        self.block_rmp_column((i,u,v,k),node_1,0)
        
        self.update_pricer((i,u,v,k),node_0,0)
        self.update_pricer((i,u,v,k),node_1,1)
        
        return {"result": SCIP_RESULT.BRANCHED}
    
    
    def branchexeclp(self, allowaddcons):
        '''executes branching rule for fractional LP solution'''
        # this method needs to be implemented by the user
        return self.branch()

    def branchexecext(self, allowaddcons):
        '''executes branching rule for external branching candidates '''
        # this method needs to be implemented by the user
        return self.branch()

    def branchexecps(self, allowaddcons):
        '''executes branching rule for not completely fixed pseudo solution '''
        # this method needs to be implemented by the user
        return self.branch()
    
    # block columns which psi_iuvk is @value, 
    def block_rmp_column(self,tuple_iuvk,node,value):
        i = tuple_iuvk[0]
        u = tuple_iuvk[1]
        v = tuple_iuvk[2]
        k = tuple_iuvk[3]
        pair = (u,v,k)
        assert(len(self.y_trans[i])==len(self.pattern_psi_u_v_k[i]))
        blocked_columns = []
        for j in range(len(self.pattern_psi_u_v_k[i])):
            if self.pattern_psi_u_v_k[i][j][pair] == value:
                blocked_columns.append(j)
       
        cons_expr = quicksum(self.y[i][j] for j in blocked_columns) == 0
        self.model.addLinearConsNode(cons_expr,node=node,stickingatnode=True)
    
    # update pricer to generate new column with psi_iuvk = @value
    def update_pricer(self,tuple_iuvk,node,value):
        i = tuple_iuvk[0]
        u = tuple_iuvk[1]
        v = tuple_iuvk[2]
        k = tuple_iuvk[3]
        name = "psi_"+str(u)+"_"+str(v)+"_"+str(k)+"_"+str(value)
        cons = self.model.createCons(self.conshdr,name,stickingatnode=True)
        self.conshdr.createData(cons,i,"psi",(u,v,k,value))
        self.model.addConsNode(node,cons)
        