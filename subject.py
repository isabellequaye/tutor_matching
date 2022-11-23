class Subject():
    def __init__(self, name, tutors_offering, tutees_requesting, number_of_tutees, number_of_tutors):
        self.name = name.strip()
        self.rarity_score = number_of_tutors-len(tutors_offering)
        self.popularity_score = number_of_tutees-len(tutees_requesting) # the lower this number, the more popular
        self.is_not_academic = name in {"Time management skills", "Career development and interview preparation", "Effective study skills"}