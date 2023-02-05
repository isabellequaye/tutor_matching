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
    class_to_tutee = {}
    for _,row in tutee_df.iterrows():
        first_class = row["Class 1"].strip()
        first_class_hours = float(row["Hours 1"])
        keberos = row['Keberos'].split("@")[0].lower()
        if first_class not in class_to_tutee:
            class_to_tutee[first_class] = [keberos]
        else:
            class_to_tutee[first_class].append(keberos)
        second_class = row["Class 2"]
        second_class_hours = row["Hours 2"]
        subject_to_hours = {first_class: first_class_hours}
        if (not pd.isnull(second_class)) and (not pd.isnull(second_class_hours)):
            second_class = second_class.strip()
            second_class_hours = float(second_class_hours)
            subject_to_hours[second_class] = second_class_hours
            if second_class not in class_to_tutee:
                class_to_tutee[second_class] = [keberos]
            else:
                class_to_tutee[second_class].append(keberos)
        tutee_object = tutee.Tutee(
                keberos, row['Name'],
                subject_to_hours, row["Timestamp"]
                )
        tutee_kerb_to_tutee_obj[keberos] = tutee_object
    return tutee_kerb_to_tutee_obj,class_to_tutee


def load_and_create_tutors(tutor_responses):
    '''
    This method reads in the csv of google responses and returns 
    a list of Tutor objects
    '''
    tutor_df = pd.read_csv(tutor_responses)
    tutor_kerb_to_tutor_obj = {}
    class_to_tutor = {}
    for _,row in tutor_df.iterrows():
        first_tier_classes = {subject_.strip() for subject_ in row["Tier 1 Classes"].split(",")}
        second_tier_classes = {subject_.strip() for subject_ in row["Tier 2 Classes"].split(",")}
        kerberos = row['Keberos'].split("@")[0].lower()
        classes =  first_tier_classes.union(second_tier_classes)

        # Parse subjects and identify any generics
        for class_ in classes:
            if class_ not in class_to_tutor:
                class_to_tutor[class_] = [kerberos]
            else:
                class_to_tutor[class_].append(kerberos)

        #Create tutor object
        tutor_object = tutor.Tutor(
                kerberos, row['Name'].strip(),
                first_tier_classes, second_tier_classes, min(_MAX_NUM_HOURS,float(row["Hours"])) # impose a max number of hours per tutor
                )
        tutor_kerb_to_tutor_obj[kerberos] = tutor_object
    return tutor_kerb_to_tutor_obj,class_to_tutor


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
        subject_obj = subject.Subject(subject_, tutors_offering[subject_], tutees, len(tutees), len(tutors_offering[subject_]))
        subject_list.append(subject_obj)
    return subject_list
        

# def refine_tutor_list_with_generics(generics_to_tutors,tutors_to_tutor_obj,subject_list):
#     '''
#     Adds specific list of course numbers to the tutors list.
#     '''
#     for course_number,tutors in generics_to_tutors.items():
#         for subject in subject_list:
#             if subject.split(".")[0] == course_number:
#                 for tutor in tutors:
#                     tutors_to_tutor_obj[tutor].subjects.add(tutor) 


def create_graph(tutor_response,tutee_response):
    '''
    Creates graph for modelling matching problem and returns node list and adjacency maps
    '''
    #Create object lists
    tutor_to_tutor_obj,subject_to_tutors = load_and_create_tutors(tutor_response)
    tutee_to_tutee_obj,subject_to_tutees = load_and_create_tutees(tutee_response)
    all_subjects = {subject.strip() for subject,_ in subject_to_tutors.items() if len(subject.strip()) != 0}
    subject_object_list = load_and_create_subjects(all_subjects,subject_to_tutors,subject_to_tutees)

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
        tutor_classes = tutor_obj.first_tier_subjects.union(tutor_obj.second_tier_subjects)
        for subject_name in tutor_classes: #outgoing edge from subject to tutor
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
                neighbours = breaking_ties.order_tutors_by_rules(neighbours, last_node)
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
        tutee_kerb = final_path[1]
        subject = final_path[2]
        tutor_kerb = final_path[3]
        if subject_to_subject_obj[subject].popularity_score < 79: #Place a cap on the number of hours if more than one student to serve
            final_cap = min(1,final_cap)
        # if subject_to_subject_obj[subject].is_not_academic:
        #     final_cap = min(0.5,final_cap)
        if not subject_to_subject_obj[subject].is_not_academic and final_cap < 1:
            tutor_cap = [cap for node,cap in residual_graph[tutor_kerb] if node=="sink"][0]
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
                tutor_to_tutor_obj[node].assign_hours(final_cap,final_path[1],subject)
            if node in tutee_to_tutee_obj:
                tutee_to_tutee_obj[node].assign_hours(final_cap,final_path[-2],subject)
    return (tutee_kerb,tutor_kerb,subject,final_cap)
 

def matching(adjacency_map,tutor_map,tutee_map,subject_map):
    '''
    Returns pairings for student  and tutee
    '''
    #Step 1: Run max flow normally using rules to break ties. 
    mappings = max_flow(adjacency_map,tutor_map,tutee_map,subject_map)

    #Step 2: Write the matched students to a file
    pm_field_names = ["Tutor Name", "Tutee Name", "Subject", "Hours","Tutor Email", "Tutee Email"]
    f = open('./primary_matching.csv', 'w')
    writer = csv.DictWriter(f,fieldnames=pm_field_names)
    writer.writeheader()
    matched_tutors = set()
    matched_tutees = set()
    for mapping in mappings:
        tutee_kerb = mapping[0]
        tutor_kerb = mapping[1]
        matched_tutors.add(tutor_kerb)
        matched_tutees.add(tutee_kerb)
        subject_ = mapping[2]
        num_hours  = mapping[3]
        writer.writerow({"Tutor Email": tutor_kerb+"@mit.edu", "Tutee Email": tutee_kerb+"@mit.edu", "Subject":subject_, "Hours":num_hours, 'Tutor Name': tutor_map[tutor_kerb].name,'Tutee Name': tutee_map[tutee_kerb].name })
    
    # Step 3: Write the unmatched students to a file and unmatched tutors to a file
    all_tutors = set(tutor_map.keys())
    all_students = set(tutee_map.keys())
    unmatched_tutors = all_tutors-matched_tutors
    unmatched_tutees = all_students-matched_tutees
    f2 = open('./unmatched_tutors.csv', 'w')
    ututor_field_names = ["Tutor Name", "Tutor Email"]
    writer2 = csv.DictWriter(f2,fieldnames=ututor_field_names)
    writer2.writeheader()
    for tutor_kerb in unmatched_tutors:
            writer2.writerow({"Tutor Email": tutor_kerb+"@mit.edu", 'Tutor Name': tutor_map[tutor_kerb].name})
    f3 = open('./unmatched_students.csv', 'w')
    ututee_field_names = ["Tutee Name", "Tutee Email"]
    writer3 = csv.DictWriter(f3,fieldnames=ututee_field_names)
    writer3.writeheader()
    for tutee_kerb in unmatched_tutees:
            writer3.writerow({"Tutee Email": tutee_kerb+"@mit.edu", 'Tutee Name': tutee_map[tutee_kerb].name})
    
    # Step 4: Close all files
    f.close()
    f2.close()
    f3.close()

if __name__ == "__main__":
    graph, tutor_map, tutee_map, subject_map = create_graph("data_/TutorResponses.csv", "data_/TuteeResponses.csv")
    matching(graph, tutor_map, tutee_map, subject_map)


