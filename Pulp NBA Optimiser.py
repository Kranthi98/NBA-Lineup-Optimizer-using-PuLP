
from pulp import *
import pandas as pd

df = pd.read_clipboard()
df = df.query("`Not Available` != 1")
num_teams = 11
salary = df.Credits.to_list()
projection = df.Projection.to_list()

set_user = range(len(df))
mandatory_players = list(df.Stack == 2)
max_mandatory_players = sum(mandatory_players)
stack_players = list(df.Stack != 0)

v = ["|".join(list(z[1])) for z in df[["Pos","Name","Credits","Projection"]].apply(lambda x : x.astype("str")).iterrows()]
u = df.Name.to_list()

def sort_players(x):
    ordered_players = []
    ordered_players = ordered_players+[y for y in x if "PG|" in y]
    ordered_players = ordered_players+[y for y in x if "SG|" in y]
    ordered_players = ordered_players+[y for y in x if "SF|" in y]
    ordered_players = ordered_players+[y for y in x if "PF|" in y]
    ordered_players = ordered_players+[y for y in x if "C|" in y]
    
    return ordered_players


name_rep = {i[0] : i[1]  for i in zip(u,v)}
diff = 0
max_points = 0
final_lineups = []
for i in range(num_teams):
    prob = LpProblem("NBA_optimizer", LpMaximize)
    
    selection = [pulp.LpVariable(f'player_{row.Name}', cat='Binary') for row in df.itertuples()]
    
    prob += lpSum(selection[i]*projection[i] for i in set_user)
    prob += lpSum(selection[i]*salary[i] for i in set_user) <= 100
    prob += lpSum(i for i in selection) == 8
    
    def get_pos_sum(selection, df, position):
        pos_filter = list(df.Pos == position)
        return lpSum(selection[i] * pos_filter[i] for i in set_user)
    
    def get_team_sum(selection, df, Team):
        pos_filter = list(df.Team == Team)
        return lpSum(selection[i] * pos_filter[i] for i in set_user)
    
    for i in df.Pos.unique():
        prob += get_pos_sum(selection, df, i) <= 4
        prob += get_pos_sum(selection, df, i) >= 1
    
    for i in df.Team.unique():
        prob += get_team_sum(selection, df, i) >= 3
        prob += get_team_sum(selection, df, i) <= 5

    if max_points != 0:
        prob += lpSum(selection[i]*projection[i] for i in set_user) <= (max_points - 0.01)
        prob += lpSum(selection[i]*mandatory_players[i] for i in set_user) >= max_mandatory_players - diff
        prob += lpSum(selection[i]*mandatory_players[i] for i in set_user) <= max_mandatory_players
        prob.solve()
        max_points = value(prob.objective)
        print("\n \n")
        print(value(prob.objective))
        lineup0 = df.assign(selection = [selection[i].varValue for i in set_user]).query("selection == 1")["Name"].replace(name_rep).to_list()
        lineup1 = sort_players(lineup0)
        lineup1 = lineup1 + [value(prob.objective)]
        final_lineups.append(lineup1)
        
    else:
        prob += lpSum(selection[i]*mandatory_players[i] for i in set_user) >= max_mandatory_players - diff
        prob += lpSum(selection[i]*mandatory_players[i] for i in set_user) <= max_mandatory_players
        prob.solve()
        status = prob.status
        if status == 1:   
            max_points = value(prob.objective)
            print("\n Optimal Solution Lineup 1\n")
            print(value(prob.objective))
            lineup0 = df.assign(selection = [selection[i].varValue for i in set_user]).query("selection == 1")["Name"].replace(name_rep).to_list()
            lineup1 = sort_players(lineup0)
            lineup1 = lineup1 + [value(prob.objective)]
            final_lineups.append(lineup1)
        else:
            print("No Optimal Solution")
            break
            
pd.DataFrame(final_lineups).to_clipboard()

