class Player:
    def __init__(self, name):
        self.name = name
        self.resources = {
            'wheat' : 0, 
            'sheep' : 0, 
            'ore' : 0, 
            'brick' : 0, 
            'wood' : 0
        }
        self.settlements = set()
        self.cities = set()
    def add_resource(self, resource, amount):
        if resource in self.resources:
            self.resources[resource]  += amount
    
    def __str__(self):
        return f"{self.name} - Resources: {self.resources}"