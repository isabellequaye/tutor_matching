#Local imports
import tutor
import tutee
import math
import subject
import breaking_ties

#foreign imports
import re
import pandas as pd
import csv

_MAX_NUM_HOURS = 4
def load_and_create_tutees(tutee_responses):
    '''
    This method reads in the google form responses and returns 
    a list of Tutee objects
    '''
    tutee_df = pd.read_csv(tutee_responses)
    tutee_kerb_to_tutee_obj = {}
    subject_to_tutee = {}
    for _,row in tutee_df.iterrows():
        subject_to_hours  = {row["Class 1"].strip():float(row["Hours 1"])}
        if row["Class 1"].strip() not in subject_to_tutee:
            subject_to_tutee[row["Class 1"].strip()] = [row['Keberos'].split("@")[0].lower()]
        else:
            subject_to_tutee[row["Class 1"].strip()].append(row['Keberos'].split("@")[0].lower())
        if (not pd.isnull(row["Class 2"])) and (not pd.isnull(row["Hours 2"])):
            subject_to_hours[row["Class 2"].strip()] = float(row["Hours 2"])
        tutee_object = tutee.Tutee(
                row['Keberos'].split("@")[0].lower(), row['Name'],
                subject_to_hours, row["Timestamp"]
                )
        tutee_kerb_to_tutee_obj[row['Keberos'].split("@")[0].lower()] = tutee_object
    return tutee_kerb_to_tutee_obj,subject_to_tutee

def load_and_create_tutors(tutor_responses):
    '''
    This method reads in the csv of google responses and returns 
    a list of Tutor objects
    '''
    tutor_df = pd.read_csv(tutor_responses)
    subject_to_tutor = {}
    tutor_kerb_to_tutor_obj = {}
    for _,row in tutor_df.iterrows():
        subjects = {subject_.strip() for subject_ in row["Academic Support"].split(",")}
        generics = set()
        kerberos = row['Keberos'].split("@")[0].lower()

        # Parse subjects and identify any generics
        for subject in subjects:
            generic_matcher = re.match("[\d]+[\.][\d]*[x]",subject)
            if generic_matcher:
                generics.add(subject)
            if subject not in subject_to_tutor:
                subject_to_tutor[subject] = [kerberos]
            else:
                subject_to_tutor[subject].append(kerberos)
        
        # Identify any non-academic support and remove empty strings
        if not pd.isnull(row["Non-academic Support"]):
            other_subjects = {other.strip() for other in row["Non-academic Support"].split(",")}
            subjects |=other_subjects
        if '' in subjects: # get rid of empty string from parsing
            subjects.remove('')

        #Create tutor object
        tutor_object = tutor.Tutor(
                kerberos, row['Name'].strip(),
                subjects, generics, min(_MAX_NUM_HOURS,float(row["Hours"])) # impose a max number of hours per tutor
                )
        tutor_kerb_to_tutor_obj[kerberos] = tutor_object
    return tutor_kerb_to_tutor_obj,subject_to_tutor

res1, res2 = load_and_create_tutors('data/TutorResponses.csv')
print(res2)


def load_and_create_subjects(subjects,tutors_offering,tutees_asking):
    '''
    Returns the list of subject objects offered this year
    '''
    subject_list = []
    for subject_ in subjects:
        if subject_ in tutees_asking:
            tutees = tutees_asking[subject_]
        else:
            tutees = []
        subject_obj = subject.Subject(subject_,tutors_offering[subject_],tutees)
        subject_list.append(subject_obj)
    return subject_list
        

def refine_tutor_list_with_generics(generics_to_tutors,tutors_to_tutor_obj,subject_list):
    '''
    Adds specific list of course numbers to the tutors list.
    '''
    for course_number,tutors in generics_to_tutors.items():
        for subject in subject_list:
            if subject.split(".")[0] == course_number:
                for tutor in tutors:
                    tutors_to_tutor_obj[tutor].subjects.add(tutor) 


def create_graph(tutor_response,tutee_response):
    '''
    Creates graph for modelling matching problem and returns node list and adjacency maps
    '''
    #Create object lists
    tutor_to_tutor_obj,subject_to_tutors,generic_course_to_tutors = load_and_create_tutors(tutor_response)
    tutee_to_tutee_obj,subject_to_tutees = load_and_create_tutees(tutee_response)
    all_subjects = {subject.strip() for subject,_ in subject_to_tutors.items() if len(subject.strip()) != 0}
    subject_object_list = load_and_create_subjects(all_subjects,subject_to_tutors,subject_to_tutees)

    #Refine tutor list to accommodate those that can teach any course eg. 7.01x, etc
    refine_tutor_list_with_generics(generic_course_to_tutors,tutor_to_tutor_obj,all_subjects)

    #Initialize graph constructs
    nodes = {"source","sink"}
    adjacency_map = {} #importantly this maps nodes to their outgoing neighbours

    #Create mappings from node names to objects
    subject_to_subject_obj = {}
    for subject_obj in subject_object_list:
        nodes.add(subject_obj.name)
        subject_to_subject_obj[subject_obj.name] = subject_obj
    #Fill up the graph with edges and vertices
    for _,tutee_obj in tutee_to_tutee_obj.items():
        nodes.add(tutee_obj.keberos)
        if "source" in adjacency_map: #outgoing edge from source to tutee
            adjacency_map["source"].add((tutee_obj.keberos,sum(tutee_obj.subject_to_hours.values())))
        else:
            adjacency_map["source"] = {(tutee_obj.keberos,sum(tutee_obj.subject_to_hours.values()))}
        for subject_name,hours in tutee_obj.subject_to_hours.items(): #outgoing edge from tutee to subject nodes
            if tutee_obj.keberos in adjacency_map:
                adjacency_map[tutee_obj.keberos].add((subject_name,hours))
            else:
                adjacency_map[tutee_obj.keberos] = {(subject_name,hours)}
    for _,tutor_obj in tutor_to_tutor_obj.items():
        nodes.add(tutor_obj.keberos)
        if tutor_obj.keberos in adjacency_map: #outgoing edge from tutor to sink nodes
            adjacency_map[tutor_obj.keberos].add(("sink",tutor_obj.hours))
        else:
            adjacency_map[tutor_obj.keberos] = {("sink",tutor_obj.hours)}
        for subject_name in tutor_obj.subjects: #outgoing edge from subject to tutor
            if subject_name in adjacency_map:
                adjacency_map[subject_name].add((tutor_obj.keberos,500))
            else:
                adjacency_map[subject_name] = {(tutor_obj.keberos,500)}
    return  adjacency_map,tutor_to_tutor_obj,tutee_to_tutee_obj,subject_to_subject_obj

def max_flow(adjacency_map,tutor_to_tutor_obj,tutee_to_tutee_obj,subject_to_subject_obj):
    pairings = []
    while True:
        match = find_path_and_construct_residual_graph(adjacency_map,tutor_to_tutor_obj,tutee_to_tutee_obj,subject_to_subject_obj)
        if match is None:
            break
        else:
            pairings.append(match)
    return pairings
        
    

def find_path_and_construct_residual_graph(residual_graph,tutor_to_tutor_obj, tutee_to_tutee_obj,subject_to_subject_obj):
    '''
    Find a path and break ties per the rules and return the residual graph
    '''
    #Queue for a depth first search
    queue = [(["source"],math.inf)]
    already_seen = set()
    #variables for keeping track of the path and capacity we find
    final_path = None
    final_cap = None
    while queue:
        curr_pair = queue.pop(0)
        curr_path = curr_pair[0]
        curr_bottleneck = curr_pair[1]
        last_node = curr_path[-1]
        already_seen.add(last_node)
        if last_node == "sink": #end once we have found a complete source to sink path
            final_path = curr_path
            final_cap = curr_bottleneck
            break
        if last_node not in residual_graph: #if node is no longer in residual graph because it has no outgoing edges, skip because it will not be useful
            continue
        else:
            if last_node == "source": #check to see if we are extending from the source and choose nodes by tie rules
                neighbours = [tutee_to_tutee_obj[n] for n,_ in residual_graph[last_node] if n in tutee_to_tutee_obj]
                neighbours_to_weights = {n:w for n,w in residual_graph[last_node]}
                neighbours = breaking_ties.order_tutees_by_rules(neighbours)
                new_paths = []
                for neighbour in neighbours:
                    if neighbour.keberos in already_seen:
                        continue
                    new_path = curr_path + [neighbour.keberos]
                    new_bottleneck = min(neighbours_to_weights[neighbour.keberos],curr_bottleneck)
                    new_paths.append((new_path,new_bottleneck))
                queue = new_paths + queue
            elif last_node in subject_to_subject_obj:
                neighbours = [tutor_to_tutor_obj[n] for n,_ in residual_graph[last_node] if n in tutor_to_tutor_obj]
                neighbours_to_weights = {n:w for n,w in residual_graph[last_node]}
                neighbours = breaking_ties.order_tutors_by_rules(neighbours)
                new_paths = []
                for neighbour in neighbours:
                    if neighbour.keberos in already_seen:
                        continue
                    new_path = curr_path + [neighbour.keberos]
                    new_bottleneck = min(neighbours_to_weights[neighbour.keberos],curr_bottleneck)
                    new_paths.append((new_path,new_bottleneck))
                queue = new_paths + queue
            elif last_node in tutee_to_tutee_obj:
                neighbours = [subject_to_subject_obj[n] for n,_ in residual_graph[last_node] if n in subject_to_subject_obj]
                neighbours_to_weights = {n:w for n,w in residual_graph[last_node]}
                neighbours = breaking_ties.order_subjects_by_rules(neighbours)
                new_paths = []
                other_paths = []
                for neighbour in neighbours:
                    if neighbour.name in already_seen:
                        continue
                    new_path = curr_path + [neighbour.name]
                    new_bottleneck = min(neighbours_to_weights[neighbour.name],curr_bottleneck)
                    if neighbour.is_not_academic:
                        other_paths.append((new_path,new_bottleneck))
                    else:
                        new_paths.append((new_path,new_bottleneck))
                queue = new_paths + queue + other_paths
            else:
                neighbours = [n for n,_ in residual_graph[last_node]]
                neighbours_to_weights = {n:w for n,w in residual_graph[last_node]}
                new_paths = []
                for neighbour in neighbours:
                    if neighbour in already_seen:
                        continue
                    new_path = curr_path + [neighbour]
                    new_bottleneck = min(neighbours_to_weights[neighbour],curr_bottleneck)
                    new_paths.append((new_path,new_bottleneck))
                queue = new_paths + queue
    if final_path is None:
        return None
    else:
        #Reduce capacities and return the match made
        if subject_to_subject_obj[final_path[2]].popularity_score < 79: #Place a cap on the number of hours if more than one student to serve
            final_cap = min(1,final_cap)
        if subject_to_subject_obj[final_path[2]].is_not_academic:
            final_cap = min(0.5,final_cap)
        if not subject_to_subject_obj[final_path[2]].is_not_academic and final_cap < 1:
            tutor_cap = [cap for node,cap in adj_map[final_path[-2]] if node=="sink"][0]
            if tutor_cap >= 1:
                final_cap = 1
        for i in range(len(final_path)-1):
            node = final_path[i]
            node_neighbours = residual_graph[node]
            current_edge = [pair for pair in node_neighbours if pair[0]==final_path[i+1]][0]
            new_weight = current_edge[1]-final_cap
            #Remove the edge to replace with a new one with new capacity
            residual_graph[node] = set([pair for pair in residual_graph[node] if pair[0] != current_edge[0]])
            if new_weight > 0:
                residual_graph[node].add((current_edge[0],new_weight))
            if node in tutor_to_tutor_obj:
                tutor_to_tutor_obj[node].received_assignment = True
                tutor_to_tutor_obj[node].assign_hours(final_cap,final_path[1])
            if node in tutee_to_tutee_obj:
                tutee_to_tutee_obj[node].assign_hours(final_cap,final_path[-2])
    return (final_path[1],final_path[-2],final_path[-3],final_cap)
 

def matching(adjacency_map,tutor_map,tutee_map,subject_map):
    '''
    Returns pairings for student  and tutee
    '''
    #Step 1: Run max flow normally using rules to break ties. 
    mappings = max_flow(adjacency_map,tutor_map,tutee_map,subject_map)
    category_A = set()
    field_names = ["Tutor Name", "Tutor Keberos", "Tutee Name", "Tutee Keberos", "Subject", "Hours","Tutor Email", "Tutee Email"]
    field_names2 = ['Tutee Name', "Tutee Keberos"]
    f = open('./Matchings.csv', 'w')
    writer = csv.DictWriter(f,fieldnames=field_names)
    writer.writeheader()
    f2 = open('./NoMatches.csv', 'w')
    writer2 = csv.DictWriter(f2,fieldnames=field_names2)
    writer2.writeheader()
    tutees = set()
    for pair in mappings:
        tutor_ = pair[1]
        tutee_ = pair[0]
        subject_ = pair[2]
        time = pair[3]
        category_A.add(tutor_)
        tutees.add(tutee_)
        writer.writerow({"Tutor Email": tutor_+"@mit.edu", "Tutee Email": tutee_+"@mit.edu", 'Tutor Keberos': tutor_, "Tutee Keberos": tutee_, "Subject":subject_, "Hours":time, 'Tutor Name': tutor_map[tutor_].name,'Tutee Name': tutee_map[tutee_].name })
    f.close()
    category_B = {(tutor_map[tutor_].name,tutor_map[tutor_].keberos) for tutor_ in tutor_map.keys() if tutor_ not in category_A}
    print(category_B)
    student_without_matchings = {tutee_map[tutee_] for tutee_ in tutee_map.keys() if tutee_ not in tutees}
    for student in student_without_matchings:
        writer2.writerow({"Tutee Name": student.name, "Tutee Keberos": student.keberos})
    f2.close()


# #Step 1: Create a graph
# adj_map,tutor_map,tutee_map,subject_map = create_graph("TutorResponses.csv", "TuteeResponses.csv")
# matching(adj_map,tutor_map,tutee_map,subject_map)



