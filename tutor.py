import student
class Tutor(student.Student):
    def __init__(self,keberos,name,first_tier_set, second_tier_set, hours) -> None:
        super().__init__(keberos,name)
        self.first_tier_subjects = first_tier_set
        self.second_tier_subjects = second_tier_set
        self.hours = hours
        self.assigned_hours = 0
        self.assigned_students_and_subject = {}
        self.received_assignment = False
    
    def assign_hours(self, hours, student, subject):
        self.received_assignment = True
        self.assigned_hours += hours
        if student in self.assigned_students_and_subject:
            subjects_and_hours = self.assigned_students_and_subject[student]
            if subject in subjects_and_hours:
                subjects_and_hours[subject] += hours
            else:
                subjects_and_hours[subject] = hours
        else:
            self.assigned_students_and_subject[student] = {subject:hours}
    
    def __str__(self):
        return "Tutor(" + self.keberos + ',' + self.name + ')'

    
    


        
