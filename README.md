# HIUTILS
## A collection of utilities for health informatics

This is pre-alpha, anything might change, i.e. not ready for production use. 

## Application areas
### Text annotation / NLP
### Ontologies
### Knowledge graphs
### Statistics / summary data

# Installation
```
pip install hiutils
```


# Annotations
## Overview
We assume that annotations are in the format:

```
{
	document_id: {
		entities: {
			entitiy_id: {
				...properties...,
				cui : "concept_id",
				meta_anns: {
					'meta_ann_name': {'value': 'meta_ann_value',
					'confidence': confidence,
					'name': 'meta_ann_name'},
					...other meta...
				}
			}
		}

	}
}
```

## Basic process
The aim is to:
1. keep only some annotations based on context
2. convert from document->concepts to patient->concepts
3. limit to a subset of concepts relevant to our project
4. group some specific concepts into more general concepts e.g. specific subtypes of a disease -> any occurence of a that disease

To achieve these aims:
* 1 filter by meta_anns:
```
filtered = hi.annotations.filter_anns_meta(anns, {'Subject': ['Other']}, inplace=False)
```
* 2 aggregate to patient level
```
agg = hi.annotations.aggregate_docs(filtered, item2doc=pt2doc)
```
* 3+4 group relevant concepts and drop other concepts
```
groups = {'Group 1': set(['286933003', '70582006']), 'My other group': set(['60046008'])}
merged = hi.merge_concepts(agg, groups, keep_empty=False)
```