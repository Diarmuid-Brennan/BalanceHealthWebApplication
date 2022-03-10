class Patient:

    firstname = ""
    lastname = ""
    age = 0
    email = ""
    condition = ""
    activities = []

    def __init__(self, firstname, lastname, age, email, condition, activities):
        self.firstname = firstname
        self.lastname = lastname
        self.age = age
        self.email = email
        self.condition = condition
        self.activities = activities

    def from_dict(source):
        patient = Patient(
            source[u"firstname"],
            source[u"lastname"],
            source[u"age"],
            source[u"email"],
            source[u"condition"],
            source[u"activities"],
        )
        return patient

    def to_dict(self):
        patient = {
            u"firstname": self.firstname,
            u"lastname": self.lastname,
            u"age": self.age,
            u"email": self.email,
            u"condition": self.condition,
            u"activities": self.activities,
        }
        return patient
