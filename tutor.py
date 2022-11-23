import student
class Tutor(student.Student):
    def __init__(self,keberos,name,subject_set, generics_set, hours) -> None:
        super().__init__(keberos,name)
        self.subjects = subject_set
        self.generics = generics_set # specifies a broad category of classes eg. 7.01x, 6.00x
        self.hours = hours
        self.assigned_hours = 0
        self.assigned_students_and_subject = {}
    
    def assign_hours(self, hours, student, subject):
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

    
    


        
