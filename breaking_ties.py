
def order_tutors_by_rules(tutorList):
    '''
    Returns a list of tutors ordered by rules
    '''
    tutor_tuples=  []
    for tutor in tutorList:
        tutor_tuple = ((tutor.received_assignment,tutor.assigned_hours,len(tutor.subjects)),tutor)
        tutor_tuples.append(tutor_tuple)
    sorted_tutor_tuples = sorted(tutor_tuples, key=lambda x:x[0])
    return [tutor for _,tutor in sorted_tutor_tuples]

def order_tutees_by_rules(tuteeList):
    '''
    Returns a list of tutees ordered by rules
    '''
    tutee_tuples = []
    for tutee in tuteeList:
        number_of_relevant = len({subject for subject in tutee.remaining_subjects if subject in {"subject_Time management skills", "subject_Career development and interview preparation", "subject_Effective study skills"}})
        tutee_tuple = ((number_of_relevant,tutee.assigned_hours,tutee.signup_time),tutee)
        tutee_tuples.append(tutee_tuple)
    sorted_tutee_tuples = sorted(tutee_tuples,key = lambda x:x[0])
    return [tutee for _,tutee in sorted_tutee_tuples]

def order_subjects_by_rules(subjectList):
    '''
    Returns subject ordered by rules
    '''
    subject_ordering = []
    for subject in subjectList:
        subject_ordering.append((subject,(subject.is_not_academic,subject.rarity_score)))
    subject_ordering.sort(key=lambda x: x[1])
    return [subject for subject,_ in subject_ordering]




    
