import student

class Tutee(student.Student):
    def __init__(self,keberos,name,subject_to_hours,signup_time) -> None:
        super().__init__(keberos,name)
        self.subject_to_hours = subject_to_hours
        self.signup_time = signup_time
        self.assigned_hours = 0
        self.assigned_tutors_and_subject = {}
        self.remaining_subjects = {subject for subject in self.subject_to_hours.keys()}
    
    def assign_hours(self,hours,tutor,subject):
        self.assigned_hours += hours
        if tutor in self.assigned_tutors_and_subject:
            subjects_and_hours = self.assigned_tutors_and_subject[tutor]
            if subject in subjects_and_hours:
                subjects_and_hours[subject] += hours
            else:
                subjects_and_hours[subject] = hours
        else:
            self.assigned_tutors_and_subject[tutor] = {subject:hours}
    
    def __str__(self):
        return "Tutee(" + self.keberos + ',' + self.name + ')'