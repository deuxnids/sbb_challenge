import json
from trains.train import Train
from resources.resource import Resource
from routes.route import Route


class Timetable(object):
    def __init__(self, json_path):
        self.trains = {}
        self.routes = {}
        self.resources = {}
        self.data = None

        with open(json_path) as f:
            data = json.load(f)
            self.data = data
            self.label = data["label"]
            self.hash = data["hash"]

            for d in data["resources"]:
                self.add_resource(Resource(data=d))

            routes = {}
            for d in data["routes"]:
                routes[d["id"]] = d

            for d in data["service_intentions"]:
                train = self.add_train(Train(data=d))
                train.network.add_route(Route(data=routes[train.get_id()], train=train))

    def add_train(self, train):
        self.trains[train.get_id()] = train
        return train

    def add_resource(self, resource):
        self.resources[resource.get_id()] = resource
