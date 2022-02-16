# functions for convenient handling of text annotations
from collections import Counter, defaultdict
import pandas as pd

# TODO
# - add confidence filter to ann and meta_ann filters
# - option to apply the count threshold before or after aggregation (i.e. do you essentially
#    set the pooled IDs to all be the same at the start or do you process separately and only
#    count those with count over thresh)
# - convenience function to handle jsonl annotations
# - in filter_meta_anns allow meta annotations below confidence threshold to be ignored in filtering
# - function to get first mention date per patient

def filter_anns_meta(anns, meta_filter, inplace = False, keep_empty = True):
	"""
	anns: dict of {document_id: {'entities': {annotation_id: {'pretty_name': '',
   'cui': '',
   'tuis': [''],
   'types': [''],
   'source_value': '',
   'detected_name': '',
   'acc': ,
   'context_similarity': ,
   'start': ,
   'end': ,
   'id': annotation_id,
   'meta_anns': {'meta_ann_type': {'value': '',
     'confidence': ,
     'name': meta_ann_type},
	 ...
	 }
	 ...
	 }
	
	meta_filter: dict {meta_name: [accepted values]}
	inplace: bool - whether the anns dict is modified in place or a modified copy is returned
			n.b. any keys other than "entities" are ignored and are NOT copied across when inplace=False
	keep_empty: bool - if False docs with no annotations after filtering will not be present in the output
	"""
	if meta_filter == None or meta_filter == {}:
		## API may change to return nothing if inplace
		return anns
	removed = 0
	kept = 0
	updated = {}
	for doc in anns:
		b = len(anns[doc]['entities'])
		filtered = {}
		for k, v in anns[doc]['entities'].items():
			keep = all([v['meta_anns'][x]['value'] in meta_filter[x] for x in meta_filter])
			if keep:
				filtered[k] = v

		if len(filtered) == 0 and keep_empty == False:
			continue

		if inplace:
			anns[doc]['entities'] = filtered
		else:
			updated[doc] = {'entities': filtered}
		removed += b - len(anns[doc]['entities'])
		kept += len(anns[doc]['entities'])
	
	if not inplace:
		return updated

def filter_anns_cui(anns, filter, inplace = False, keep_empty = True):
	"""
	Filter annotations to only retain those in filter
	"""
	if filter == None or filter == {}:
		if not inplace:
			return anns
		#in this case explicitly return None to stop execution here
		return None
	removed = 0
	kept = 0
	updated = {}
	for doc in anns:
		b = len(anns[doc]['entities'])
		filtered = {k:v for k, v in anns[doc]['entities'].items() if v['cui'] in filter}

		if len(filtered) == 0 and keep_empty == False:
			continue

		if inplace:
			anns[doc]['entities'] = filtered
		else:
			updated[doc] = {'entities': filtered}
		removed += b - len(anns[doc]['entities'])
		kept += len(anns[doc]['entities'])
	
	if not inplace:
		return updated

def filter_anns(anns, filter = None, meta_filter = None, inplace=False, keep_empty = True):
	anns = filter_anns_meta(anns, meta_filter, inplace, keep_empty)
	anns = filter_anns_cui(anns, filter, inplace, keep_empty)
	return anns

def aggregate_docs(anns, item2doc = None, doc2item = None, keep_empty = True):
	"""
	anns should be pre-filtered so all annotations can be included in the aggregated data
	item could be a patient ID, an admission ID, a ward stay ID

	keep_empty: bool - if False then empty items are not included in the returned dict (i.e. patients with documents but no annotations will not be present in output)
	"""
	if item2doc == None and doc2item == None:
		return
	if item2doc != None and doc2item != None:
		return
	
	#if we only got doc2item, invert the map
	if doc2item != None:
		item2doc = defaultdict(list)
		for doc, item in doc2item.items():
			item2doc[item].append(doc)
		item2doc = dict(item2doc)

	aggregated = {}
	if item2doc != None:
		for pt, docs in item2doc.items():
			count = Counter()
			for doc in docs:
				doc_anns = anns.get(doc, {'entities':{}})
				count.update([x['cui'] for x in doc_anns['entities'].values()])
			if len(count) == 0 and keep_empty == False:
				continue
			aggregated[pt] = dict(count)
	
	return aggregated
		
	

def merge_concepts_docs(anns, groups, inplace=False):
	"""
	return a copy of the annotations with the grouping applied
	groups: dict - {group_name: [contained CUI]}. Must be 1:1 CUI:Group.
	to keep the structure consistent with raw annotations the output only replaces the grouped CUI with the group name
	this is only useful to allow subsequent aggregation of concepts when you don't aggregate docs to some other unit e.g. patient
	May be a more convenient way to handle aggregation of concepts if you need multiple different groupings of documents
	"""
	#invert the groups
	cui2group = {}
	for name, cuis in groups.items():
		for c in cuis:
			cui2group[c] = name
	
	aggregated = {}
	# for doc, ann in anns.items():
	# 	doc_cui = Counter([x['cui'] for x in ann['entities']])
	# 	agg = {}
	# 	i = 0
	# 	for group_name, group_cui in groups.items():
	# 		total = sum(doc_cui[x] for x in group_cui)
	# 		if total != 0:
	# 			agg[i] = {'cui': group_name}

	for doc, ann in anns.items():
		update = {}
		for k, v in ann['entities'].items():
			if v['cui'] in cui2group:
				if inplace:
					update[k] = v
				else:
					update[k] = v.copy()
				update[k]['cui'] = cui2group[v['cui']]
		if not inplace:
			aggregated[doc] = {'entities': update}
	
	if not inplace:
		return aggregated

def merge_concepts(anns_counts, groups, keep_other_concepts=False, keep_empty = True):
	"""
	anns_counts: dict - output of aggregated annotations 
	groups: dict - {group_name: [contained CUI]}. Must be 1:1 CUI:Group.
	keep_other_concepts: bool - if False concepts that are not in a group are not returned in the output
	keep_empty: bool - if false keys in anns_counts with no entries after aggregation will not be returned
	"""

	aggregated = {}
	other_concepts = set()
	for cuis in groups.values():
		other_concepts.update(cuis)
	
	for pt, counts in anns_counts.items():
		agg = {}
		for name, cuis in groups.items():
			total = sum([counts[x] for x in cuis if x in counts])
			if total != 0:
				agg[name] = total
		if keep_other_concepts:
			others = {x:counts[x] for x in counts if x in other_concepts}
			agg.update(others)
		if len(agg) == 0 and keep_empty == False:
			continue
		aggregated[pt] = agg
	
	return aggregated

def anns_counts_to_dataframe(anns_counts, min_count = None):
	"""
	convert aggregated annotations to an item-level bool dataframe by applying min_count
	anns_counts: dict - {item_id: {concept_id: count}} i.e. output of aggregate_docs
	min_count: int or None - minimum number of times a concept must be detected to count as True. If None then return the count.
	"""

	df = pd.DataFrame(anns_counts).T
	if min_count != None:
		df = df >= min_count
	return df

			

def count_anns(anns):
	"""
	anns: dict { doc_id: entities: { ... }}
	"""
	count = sum([len(x['entities']) for x in anns.values()])
	return count
