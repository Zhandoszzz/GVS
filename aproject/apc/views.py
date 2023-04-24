from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import CreateView
from neo4j import GraphDatabase
import json
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse_lazy
from .models import *

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neo4j"))


def get_graph(tx, info):
    query = ''
    typeOf = info.get('type', [True])[0]
    node1 = info.get('node1', [None])[0]
    node2 = info.get('node2', [None])[0]
    limit = info.get("limit", [None])[0]
    level = info.get("level", [None])[0]
    all_relations = info.get("all_relations", [False])[0]
    relations = info.get("relations", [None])
    relation_types = ""

    if not all_relations:
        if not relations[0]:
            return None
        relation_types = ":"
        for rel in relations[:-1]:
            relation_types += rel + "|"
        relation_types += relations[-1]
    if level:
        level = "*.." + level
    else:
        level = "*"
    if typeOf == True:
        return None
    elif typeOf == "P-M":
        query = f"MATCH (n1:Person {{name: \"{node1}\"}}), (n2:Movie {{title: \"{node2}\"}}), p = allShortestPaths((n1) - [{relation_types}{level}] - (n2)) RETURN p"
    elif typeOf == 'P-P':
        query = f"MATCH (n1:Person {{name: \"{node1}\"}}), (n2:Person {{name: \"{node2}\"}}), p = allShortestPaths((n1) - [{relation_types}{level}] - (n2)) RETURN p"
    elif typeOf == 'M-M':
        query = f"MATCH (n1:Movie {{title: \"{node1}\"}}), (n2:Movie {{title: \"{node2}\"}}), p = allShortestPaths((n1) - [{relation_types}{level}] - (n2)) RETURN p"
    elif typeOf == 'P':
        if level == "*":
            level = ""
        query = f"match (p) - [r{relation_types}{level}] - (m:Person {{name: \"{node1}\"}}) return m, p, r"
    elif typeOf == 'M':
        if level == "*":
            level = ""
        query = f"match (p) - [r{relation_types}{level}] - (m:Movie {{title: \"{node1}\"}}) return m, p, r"
    if limit:
        query += f" limit {limit}"
    print(query)
    result = tx.run(query)
    return result.graph()


def visualize_result(query_graph, nodes_text_properties):
    visual_graph = {"Nodes": [], "Edges": []}

    for node in query_graph.nodes:
        node_label = list(node.labels)[0]
        node_text = node[nodes_text_properties[node_label]]
        node_title = ""
        for x in node:
            node_title += x + ": " + str(node[x]) + "\\n"
        visual_graph["Nodes"].append({"id": node.element_id,
                                      "label": node_text,
                                      "group": node_label,
                                      "shape": "dot",
                                      "title": node_title})

    for relationship in query_graph.relationships:
        relationship_title = ""
        for x in relationship:
            relationship_title += x + ": " + str(relationship[x]) + "\\n"

        visual_graph["Edges"].append({"from": relationship.start_node.element_id,
                                      "to": relationship.end_node.element_id,
                                      "label": relationship.type,
                                      "title": relationship_title})

    return visual_graph

def index(request):
    if not request.user.is_authenticated:
        return render(request, "apc/index.html")

    if request.method == 'GET':
        info = dict(request.GET)
        print(info)
        if request.user.is_authenticated:
            user = request.user
            qs = Query()
            qs.query = (info.get("node1","") + info.get("node2",""))
            qs.user = user
            qs.save()
        with driver.session(database="neo4j") as session:
            graph = session.execute_read(get_graph, info)
            if not graph:
                return render(request, "apc/index.html")
        nodes_text_properties = {
            "Person": "name",
            "Movie": "title",
        }
        graph = visualize_result(graph, nodes_text_properties)
        graph = json.dumps(graph)
    return render(request, "apc/index.html", {'graph': graph})

class RegisterUser(CreateView):
    form_class = UserCreationForm
    template_name = "apc/register.html"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('index')

    def get_success_url(self):
        return reverse_lazy('index')

class LoginUser(LoginView):
    form_class = AuthenticationForm
    template_name = "apc/login.html"

    def get_success_url(self):
        return reverse_lazy('index')

def logout_user(request):
    logout(request)
    return redirect('index')


driver.close()
