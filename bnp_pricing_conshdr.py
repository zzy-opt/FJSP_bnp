from pyscipopt import Model, Pricer, Conshdlr, SCIP_RESULT, SCIP_PARAMSETTING, quicksum
from fjspim_problem import FJSPIMProblem
from fjspim_model import FJSPIMModel
from bnp_pricer import SchedulePricer

        
class PricingDataHdr(Conshdlr):

    def __init__(self,p_data,y):
        self.nodes = 0
        self.data = {}
        # pricer data
        self.data["p_data"] = p_data
        self.y = y
        
    # machine = i, var_name = "lamda" or "psi", var_tuple = "u,k,value" or "u,v,k,value"   
    
    def createData(self, constraint, machine,var_name, var_tuple,node,pattern):
        #print("add new pricer data, var:{}".format(var_name))
        
        constraint.data = {}
        assert((var_name == "lamda" and len(var_tuple)==3) or (var_name == "psi" and len(var_tuple)==4))
        constraint.data["var_name"] = var_name
        constraint.data["var_tuple"] = var_tuple
        constraint.data["machine"] = machine
        constraint.data["node"] = node
        constraint.data["pattern"] = pattern
        
    ## fundamental callbacks ##
    def consenfolp(self, constraints, nusefulconss, solinfeasible):
        return {"result": SCIP_RESULT.FEASIBLE}

    def conscheck(self, constraints, solution, checkintegrality, checklprows, printreason, completely):
        return {"result": SCIP_RESULT.FEASIBLE}

    def conslock(self, constraint, locktype, nlockspos, nlocksneg):

        return {"result": SCIP_RESULT.SUCCESS}
    
    def consenforelax(self, solution, constraints, nusefulconss, solinfeasible):
        
        return {"result": SCIP_RESULT.FEASIBLE}
    
    def consenfops(self, constraints, nusefulconss, solinfeasible, objinfeasible):
        
        return{"result": SCIP_RESULT.SOLVELP}
    
    ## callbacks ##

    def consinit(self, constraints):
        1

    def consexit(self, constraints):
        1

    # consresprop

    def consactive(self, constraint):
        self.nodes = self.nodes + 1
        print(self.nodes)
        if constraint.data["var_name"]=="lamda":
            self.data["p_data"]["fixed_lamda"][constraint.data["machine"]].append(constraint.data["var_tuple"])
            tuple_iuk = (constraint.data["machine"],constraint.data["var_tuple"][0],constraint.data["var_tuple"][1])
            value = (1-constraint.data["var_tuple"][2])
            self.block_rmp_column_lamda(tuple_iuk,constraint.data["node"],value,constraint.data["pattern"])
            #print("fixing lamda_{}_{} with value {}".format(constraint.data["var_tuple"][0],constraint.data["var_tuple"][1],constraint.data["var_tuple"][2]))
        else:
            self.data["p_data"]["fixed_psi"][constraint.data["machine"]].append(constraint.data["var_tuple"])
            tuple_iuvk = (constraint.data["machine"],constraint.data["var_tuple"][0],constraint.data["var_tuple"][1],constraint.data["var_tuple"][2])
            value = (1-constraint.data["var_tuple"][3])
            self.block_rmp_column_psi(tuple_iuvk,constraint.data["node"],value,constraint.data["pattern"])
            
            #print(self.data["p_data"]["fixed_lamda"][constraint.data["machine"]])
    def consdeactive(self, constraint):
        if constraint.data["var_name"]=="lamda":
            assert(len(self.data["p_data"]["fixed_lamda"][constraint.data["machine"]]) > 0)
            poped = self.data["p_data"]["fixed_lamda"][constraint.data["machine"]].pop()
            #print("unfixing lamda_{}_{}  with value {}".format(poped[0],poped[1],poped[2]))
        else:
            assert(len(self.data["p_data"]["fixed_psi"][constraint.data["machine"]]) > 0)
            self.data["p_data"]["fixed_psi"][constraint.data["machine"]].pop()

    def consenable(self, constraint):
        1

    def consdisable(self, constraint):
        1

    def block_rmp_column_lamda(self,tuple_iuk,node,value,pattern):
        i = tuple_iuk[0]
        u = tuple_iuk[1]
        k = tuple_iuk[2]
        pair = (u,k)
        assert(len(self.y[i])==len(pattern[i]))
        blocked_columns = []
        for j in range(len(pattern[i])):
            #print("i:{},j:{},pair:{}".format(i,j,pair))
            if value == 0:
                if pair in pattern[i][j]:
                    if pattern[i][j][pair] == value:
                        blocked_columns.append(j)
                else:
                    blocked_columns.append(j)
            else: 
                assert(value == 1)
                if pair in pattern[i][j]:
                    if pattern[i][j][pair] == value:
                        blocked_columns.append(j)
        
        # try_to_add_cons_node
        # should i fix transformed or orginal variables
        """
        can not be done like this, the node where cons is added must be specified 
        m.addCons(quicksum(self.y[i][j] for j in blocked_columns) == 0,
                                             name = "fix"+str(i)+"_"+str(u)+"_"+str(k), stickingatnode = True)    
        """
        for j in blocked_columns:
            self.model.chgVarUbNode(node,self.y[i][j],0)
        

    def block_rmp_column_psi(self,tuple_iuvk,node,value,pattern):
        i = tuple_iuvk[0]
        u = tuple_iuvk[1]
        v = tuple_iuvk[2]
        k = tuple_iuvk[3]
        pair = (u,v,k)
        assert(len(self.y[i])==len(pattern[i]))
        blocked_columns = []
        for j in range(len(pattern[i])):
            if value == 0:
                if pair in pattern[i][j]:
                    if pattern[i][j][pair] == value:
                        blocked_columns.append(j)
                else:
                    blocked_columns.append(j)
            else: 
                assert(value == 1)
                if pair in pattern[i][j]:
                    if pattern[i][j][pair] == value:
                        #print("block psi:{}".format(j))
                        blocked_columns.append(j)
                        
       
        #cons_expr = quicksum(self.y[i][j] for j in blocked_columns) == 0
        #self.model.addLinearConsNode(cons_expr,node=node,stickingatnode=True)
        for j in blocked_columns:
            self.model.chgVarUbNode(node,self.y[i][j],0)
        