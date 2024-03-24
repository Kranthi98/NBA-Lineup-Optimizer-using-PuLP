from pulp import *
import pandas as pd
from datetime import datetime

#reading the data
df = pd.read_clipboard()
df = df.query("Exclude != 1")

#getting the unique teams
teams = df.Team.unique()

#Storing the player credits
salary = df.Credits.to_list()

#Storing the projections
projection = df.Projection.to_list()
num_lineups = 20 #Number of lineups to be generated

#Working on exposure numbers
props = round((df.Exposure*num_lineups),0).to_dict()
props = {x : props[x] for x in props.keys() if props[x] > 0 }
proj = dict()
sal = dict()
for i in range(len(df)):
    for j in range(num_lineups):
        proj[(i,j)] = projection[i]
        sal[(i,j)] = salary[i]        
start=datetime.now()

#Setting up the optimisation problem
prob = LpProblem("NBA_optimizer", sense = LpMaximize)

#Choice variables
choices = LpVariable.dicts("choice",((i,j)  for j in range(num_lineups) for i in range(len(df))), cat = LpBinary)

#Adding objective
objective = lpSum([choices[i, j] * proj[i,j] for i, j in choices])
prob += objective
cur_lineup = 0
prev_lineup = 0
for j in range(num_lineups):

    #8-Member Lineup Constraint
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],1) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintEQ,
                             rhs = 8)
    prob.addConstraint(tempConst)
    
    #Constraint on Credits - Should not exceed 100
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],sal[i,j]) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintLE,
                             rhs = 100)
    prob.addConstraint(tempConst)
    
    #Minimum and Maximum constraint from single team
    team_filter = list(df.Team == teams[0])
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],team_filter[i]) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE,
                             rhs = 3)
    prob.addConstraint(tempConst)
    
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintLE,
                             rhs = 5)
    prob.addConstraint(tempConst)
    
    #Position Constraints - PG Min of 1 and Max of 4
    pos_filter = list(df.Pos == "PG")
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],pos_filter[i]) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE,
                             rhs = 1)
    prob.addConstraint(tempConst)
    
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintLE,
                             rhs = 4)
    prob.addConstraint(tempConst)
    
    #Position Constraints - SG Min of 1 and Max of 4
    pos_filter = list(df.Pos == "SG")
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],pos_filter[i]) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE,
                             rhs = 1)
    prob.addConstraint(tempConst)
    
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintLE,
                             rhs = 4)
    prob.addConstraint(tempConst)
    
    #Position Constraints - SF Min of 1 and Max of 4
    pos_filter = list(df.Pos == "SF")
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],pos_filter[i]) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE,
                             rhs = 1)
    prob.addConstraint(tempConst)
    
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintLE,
                             rhs = 4)
    prob.addConstraint(tempConst)
    
    #Position Constraints - PF Min of 1 and Max of 4
    pos_filter = list(df.Pos == "PF")
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],pos_filter[i]) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE,
                             rhs = 1)
    prob.addConstraint(tempConst)
    
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintLE,
                             rhs = 4)
    prob.addConstraint(tempConst)
    
    #Position Constraint - C Min of 1 and Max of 4
    pos_filter = list(df.Pos == "C")
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],pos_filter[i]) for i in range(len(df))])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE,
                             rhs = 1)
    prob.addConstraint(tempConst)
    
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintLE,
                             rhs = 4)
    prob.addConstraint(tempConst)
    
    #Constraint to make sure that no two lineups will have same set of players.
    if j > 0:
        tempExp = pulp.LpAffineExpression(e = [(choices[i,j],proj[i,j]) for i in range(len(df))] + [(choices[i,j-1],-proj[i,j]) for i in range(len(df))])
        tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE,
                                 rhs = 0.001)
        prob.addConstraint(tempConst)

            
#Naive Run
print("Runnings Naive Run")
prob.solve(PULP_CBC_CMD(msg=1,timeLimit = 600, threads = 10))
print(prob.status)

for i in props.keys():
    tempExp = pulp.LpAffineExpression(e = [(choices[i,j],1) for j in range(num_lineups)])
    tempConst = LpConstraint(e = lpSum(tempExp), sense = LpConstraintGE, rhs = props[i])  
    prob.addConstraint(tempConst)
print("Running with Player Constraints on Exposure")
prob.solve(PULP_CBC_CMD(msg=1,timeLimit = 600, threads = 10))
print(prob.status)
    


#Statements
def sort_players(x):
    ordered_players = []
    ordered_players = ordered_players+[y for y in x if "PG)" in y]
    ordered_players = ordered_players+[y for y in x if "SG)" in y]
    ordered_players = ordered_players+[y for y in x if "SF)" in y]
    ordered_players = ordered_players+[y for y in x if "PF)" in y]
    ordered_players = ordered_players+[y for y in x if "C)" in y]
    
    return ordered_players

if prob.status == 1:
    print("Found the Optimal Solution")
    print("Time Taken for optimisation : ", datetime.now()-start)


    import numpy as np
    selections = np.zeros((len(df), num_lineups))
    for i in range(len(df)):
        for j in range(num_lineups):
            selections[i,j] = choices[i,j].varValue     
        
    d0 = pd.DataFrame(selections, columns = ["lineup_"+str(i+1) for i in range(num_lineups)]).assign(Player = "("+df.Pos+")-"+df.Name)
    
    lineup_list = []
    for i in range(num_lineups):
        lineup_list.append(sort_players(d0.query(f"lineup_{i+1} == 1").Player.to_list()))
else:
    print("Unable to find the Optimal Solution.. :(")
    print("Time Taken for optimisation : ", datetime.now()-start)

pd.DataFrame(lineup_list).to_clipboard()
