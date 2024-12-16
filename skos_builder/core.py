import re
from typing import Literal as LiteralType
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import (
    _NAMESPACE_PREFIXES_CORE,
    _NAMESPACE_PREFIXES_RDFLIB,
    RDF,
    SKOS,
    Namespace,
)

from .translate import get_translations_for_string

all_namespaces = {**_NAMESPACE_PREFIXES_CORE, **_NAMESPACE_PREFIXES_RDFLIB}


def slugify(value):
    """Slugifies a string."""
    value = " ".join(re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", value)).lower()
    return value.replace(" ", "-")


def get_uriref(curie):
    prefix, name = curie.split(":")
    namespace = all_namespaces[prefix]
    return namespace[name]


class Options:
    name = ""
    """The name of the vocabulary. This is used to internally identify the vocabulary for things like URL routing. Should be url-safe."""

    prefix = ""
    """The prefix for the vocabulary. This is used to namespace all concepts in the vocabulary."""

    base_url = ""
    """The root namespace for the vocabulary. This is used to namespace all concepts in the vocabulary. It should be a valid URI."""

    namespace_separator: LiteralType["#", "/"] = "#"

    scheme = ""

    collections = []

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k.startswith("_"):
                continue
            elif getattr(self, k, None) is None:
                msg = f"Invalid Meta option: {k}"
                raise AttributeError(msg)
            else:
                setattr(self, k, v)


class Concept(dict):
    defaults = {RDF.type: SKOS.Concept}
    name = ""

    def __init__(self, attrs, name=None, **kwargs):
        self.name = name
        self.defaults.update(attrs)
        super().__init__(**self.defaults)

    def __getitem__(self, key):
        if not isinstance(key, URIRef):
            key = get_uriref(key)
        return super().__getitem__(key)

    def as_graph(self, subject=None, graph=None):
        graph = graph if graph is not None else Graph()
        subject = subject if subject else BNode()
        for p, o in self.items():
            self._add_triple(graph, subject, p, o)
        return graph

    def _add_triple(self, graph, subject, p, o):
        if not isinstance(p, URIRef):
            p = get_uriref(p)

        if isinstance(o, URIRef):
            graph.add((subject, p, o))

        elif isinstance(o, list):
            for entry in o:
                self._add_triple(graph, subject, p, entry)
        else:
            for lang, msg in get_translations_for_string(o).items():
                graph.add((subject, p, Literal(msg, lang=lang)))


class Collection(Concept):
    defaults = {RDF.type: SKOS.Collection}
    orderer = False


class ConceptScheme(Concept):
    defaults = {RDF.type: SKOS.ConceptScheme}


class SKOSBuilder(object):
    def __init__(self):
        self._meta = Options(**self.Meta.__dict__)
        self.name = self._meta.name or slugify(self.__class__.__name__)
        self.ns = Namespace(
            self._meta.base_url + self.name + self._meta.namespace_separator
        )
        self.build_graph()
        self.graph.bind(self._meta.prefix, self.ns)
        self._meta.scheme.as_graph(URIRef(self._meta.base_url + self.name), self.graph)

    def build_graph(self):
        self.graph = Graph()
        terms = self.__class__.__dict__
        for name, attrs in terms.items():
            if isinstance(attrs, Concept):
                self.add_term(name, attrs)

    def add_term(self, name, term):
        # if the term has explicitly set name, use that
        name = name if not term.name else term.name

        # if the name has spaces, url-encode it
        if " " in name:
            name = quote(name)

        # if the name is not a URIRef, make it one
        if not isinstance(name, URIRef):
            name = self.ns[name]

        # add the term to the graph
        term.as_graph(name, self.graph)

    def serialize(self, **kwargs):
        return self.graph.serialize(**kwargs)
