from pyscipopt import Model, Pricer,Branchrule, SCIP_RESULT, SCIP_PARAMSETTING, quicksum
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_pricer import SchedulePricer
from bnp_constant import INTEGER_PRECISION
from bnp_conshdr import PricingDataHdr


class BranchingAssignment(Branchrule):

    # p problem, y convexity variables in rmp, patter, conshdr
    def __init__(self,p,y,pattern_lamda_u_k, conshdr):
        print("initialize branching rule")
        self.p = p
        self.y = y
        self.pattern_lamda_u_k = pattern_lamda_u_k
        self.conshdr = conshdr
        

    def branchinitsol(self):
        print("branchinitsol")
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
    
    
    def find_binary_lamda(self):
        # initialize all lamda_u_k to 0
        sum_lamda_u_k = {}
        for i in self.p.M:
            for u in self.p.D[i]:
                for k in self.p.K[i]:
                    sum_lamda_u_k[(u,k)] = 0
                    
        for i in self.p.M:
            assert(len(self.y_trans[i])==len(self.pattern_lamda_u_k[i]))
            for j in range(len(self.y_trans[i])):
                y_ij = self.y_trans[i][j].getLPSol()
                for pair in self.pattern_lamda_u_k[i][j]:
                    sum_lamda_u_k[pair] = sum_lamda_u_k[pair] + self.pattern_lamda_u_k[i][j][pair] * y_ij
                    
        for i in self.p.M:
            for u in self.p.D[i]:
                for k in self.p.K[i]:
                    if __isfractional(sum_lamda_u_k[(u,k)]):
                        return (i,u,k)
        return 0
    
    
    def branch(self):
        
        print("check branching lp")
        
        tuple_iuk = find_binary_lamda()
        if len(tuple_iuk) == 1:
            return {"result": SCIP_RESULT.DIDNOTRUN}
        assert(len(tuple_iuk) == 3)
        i = tuple_iuk[0]
        u = tuple_iuk[1]
        k = tuple_iuk[2]
        assert(i in self.p.M)
        assert(u in self.p.D[i])
        assert(k in self.p.K[i])
        
        node_0 = self.model.createChild(0.0,self.model.getLocalEstimate())
        node_1 = self.model.createChild(0.0,self.model.getLocalEstimate())
        
        self.block_rmp_column((i,u,k),node_0,1)
        self.block_rmp_column((i,u,k),node_1,0)
        
        self.update_pricer((i,u,k),node_0,0)
        self.update_pricer((i,u,k),node_1,1)
        
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
    
    # block columns which lamda_iuk is @value, 
    def block_rmp_column(self,tuple_iuk,node,value):
        i = tuple_iuk[0]
        u = tuple_iuk[1]
        k = tuple_iuk[2]
        pair = (u,k)
        assert(len(self.y_trans[i])==len(self.pattern_lamda_u_k[i]))
        blocked_columns = []
        for j in range(len(self.pattern_lamda_u_k[i])):
            if self.pattern_lamda_u_k[i][j][pair] == value:
                blocked_columns.append(j)
        
        # try_to_add_cons_node
        # should i fix transformed or orginal variables
        """
        can not be done like this, the node where cons is added must be specified 
        m.addCons(quicksum(self.y[i][j] for j in blocked_columns) == 0,
                                             name = "fix"+str(i)+"_"+str(u)+"_"+str(k), stickingatnode = True)    
        """
        cons_expr = quicksum(self.y[i][j] for j in blocked_columns) == 0
        self.model.addLinearConsNode(cons_expr,node=node,stickingatnode=True)
    
    # update pricer to generate new column with lamda_iuk = @value
    def update_pricer(self,tuple_iuk,node,value):
        i = tulple_iuk[0]
        u = tulple_iuk[1]
        k = tulple_iuk[2]
        name = "lamda_"+str(u)+"_"+str(k)+"_"+str(value)
        cons = self.model.createCons(self.conshdr,name,stickingatnode=True)
        self.conshdr.createData(cons,i,"lamda",(u,k,value))
        self.model.addConsNode(node,cons)
        
        
        