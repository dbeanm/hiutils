#Patient
#Concept (one or more CUI)
#only really need first mention date?
#pt->doc->cui? or pt->cui? the reason to go via doc would be:
# - only specific docs should count - date, type, quality, etc
# - the date filter can be achieved with a first mention date on the pt->cui edge, the others cannot be approximated
# implement both options? Or one graph with both types of edge?
# load anns to an internal KG, then use that to give Patient objects? e.g. that meet certain criteria?
# this is for static data

##
# can Patient be implemented such that properties are easily found from them?
# e.g. patient has a pointer to it's docs, those point to it's CUI? 

from collections import defaultdict
from tkinter import E

class Patient():
	#must be hashable to be a nx node but could use Patient as a property of a node
	#with the ID set to patient id
	### how does lookup by ID work if nodes are custom classes?
	### may need to also add lookup values e.g. id as properties in nx
	def __init__(self, id):
		self.id = id

class Document():
	def __init__(self, id):
		self.id = id

class Concept():
	def __init__(self, id):
		self.id = id

#the idea is you can provide Phenotypes (which are sets of concepts that must/not be present)
#and apply them to the graph - all Patient nodes will then be updated with presence of that phenotype
#you can then get all patients or only those with certain Phenotypes

class PatientGraph():
	# TODO
	# - throughoutt, check that nodes exist before creating edge. Currently I know they will exist first but
	#   can't assume in general
	# - only create nodes if the id doesn't already exist - in case metadata had been added. Currently always
	#   overwrite for eases
	# Notes
	# - if all the nodes/edges were in one object each, all patients with a parent concept in the ontology could
	#   be found by one call to Directed.descendants from that ontology node. Would be interesting to know
	#   if there was a major performance difference.
	def __init__(self):
		self.nodes = {'Patient': {}, 'Document': {}, 'Concept': {}}
		self.edges = {
			'patient_to_document': Directed(),
			'document_to_concept': Directed(),
			'ontology': Directed()
		}

	def load_anns(self, anns, pt2docs):
		for pt, docs in pt2docs.items():
			self.nodes['Patient'][pt] = Patient(pt)
			for doc in docs:
				self.nodes['Document'][doc] = Document(doc)
				self.edges['patient_to_document'].add(pt, doc)
		for doc in anns:
			for k, v in anns[doc]['entities'].items():
				self.nodes['Concept'][v['cui']] = Concept(v['cui'])
				self.edges['document_to_concept'].add(doc, v['cui'])
		print('Loaded nodes:')
		for node_type in self.nodes:
			print(node_type, ' - ', len(self.nodes[node_type]))
		print('Loaded edges:')
		for edge_type in self.edges:
			print(edge_type, ' - ', len(self.edges[edge_type]))
	
	def load_ontology(self, edges):
		for e in edges:
			for n in e:
				self.nodes['Concept'][n] = Concept(n)
			self.edges['ontology'].add(e[0], e[1])
	
	def get_patient_concepts(self, patient):
		if patient not in self.nodes['Patient']:
			raise ValueError("id", patient, "not found in patient nodes")
		
		pt_docs = self.edges['patient_to_document'][patient]
		concepts = set()
		for doc in pt_docs:
			concepts.update(self.edges['document_to_concept'][doc])
		
		return concepts
	
	def add_patient_meta():
		pass

	def add_doc_meta():
		pass

	def apply_phenotype():
		#update all Patient nodes with the new phenotype
		pass

	#some load as / convert to condensed graph
	#maybe as a separate class?
	# with only patient - HAS -> concept 
	# and the first and last metion dates recorded so date filters can be applied


class Undirected():
	def __init__(self):
		self.edges = defaultdict(set)
	
	def add(self, a, b):
		self.edges[a].add(b)
		self.edges[b].add(a)
	
	def has_edge(self, a, b):
		if a in self.edges:
			return b in self.edges[a]
		return False
	
	def __len__(self):
		return int(sum([len(x) for x in self.edges]) / 2)

class Directed():
	def __init__(self):
		self.edges = defaultdict(set)
		self.edges_rev = defaultdict(set)
	
	def add(self, source, target):
		if target in self.edges and source in self.edges[target]:
			raise ValueError("the edge {}->{} already exists in the reverse direction".format(source, target))
		self.edges[source].add(target)
		self.edges_rev[target].add(source)
	
	def has_edge(self, source, target):
		if source in self.edges:
			return target in self.edges[source]
		return False
	
	def descendants(self, code, reverse=False, include_self=False):
		#if reverse==True then follow edges from target to source i.e. in reverse
		found = set()
		todo = set()
		todo.add(code)
		done = set()
		while len(todo) != 0:
			n = todo.pop()
			#using a defaultdict so accessing something not present will add it with an empty set
			#instead use in first
			if n in self.edges:
				ch = self.edges[n]
				new = ch.difference(done)
				todo = todo.union(new) #or equivalently todo |= ch
				found.update(ch)
			done.add(n)
		return found
	
	def __len__(self):
		return int(sum([len(x) for x in self.edges]))
	
	def __getitem__(self, key):
		if key not in self.edges:
			#normally this should raise a KeyError
			return set()
		return self.edges[key]



