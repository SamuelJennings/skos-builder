# from django.utils import translation
# from django.utils.safestring import SafeString
# from django.utils.translation import trans_real
import importlib
import inspect
import os

from rdflib import Graph, URIRef

from .core import SKOSBuilder


class LocalFilePathError(Exception):
    """Exception raised when a ConceptScheme subclass cannot find its source file."""

    def __init__(self, klass):
        message = f"{klass} - no source file exists at the specified location"
        super().__init__(message)


class RemoteURLError(Exception):
    """Exception raised when a ConceptScheme subclass cannot find its source file."""

    def __init__(self, class_name, url):
        message = f"{class_name} remote source URL <{url}> is not valid"
        super().__init__(message)


def get_URIRef(val: str | URIRef, graph: Graph, ns):
    """
    Normalizes val to a URIRef object.

    Args:
        val (str | URIRef): The value to be normalized. It can be a URI string, a valid CURIE (e.g. "SKOS:Concept"), or a URIRef object.
        graph (Graph): The graph object used for expanding CURIEs.

    Returns:
        URIRef: A URIRef object.

    """
    # calling .strip() on a SafeString will convert to regular python str
    # if isinstance(val, SafeString):
    # val = val.strip()

    if isinstance(val, URIRef):
        return val
    elif val.startswith("http"):
        return URIRef(val)
    elif ":" in val:
        return graph.namespace_manager.expand_curie(val)
    else:
        return ns[val]


def vocabs_from_module(module):
    """
    Function to extract all vocabularies from a module.

    Args:
        module: The module to extract vocabularies from.

    Returns:
        list: A list of all vocabularies in the module.

    """
    # List to store subclasses
    subclasses = []

    # Iterate through all classes in the module
    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and issubclass(obj, SKOSBuilder)
            and obj is not SKOSBuilder
        ):
            subclasses.append(obj)

    return subclasses


def export_vocabs(module: str, output_dir: str, format="ttl"):
    """
    Function to export a list of vocabularies to a specified format.

    Args:
        vocabs (list): A list of vocabularies to export.
        format (str): The format to export the vocabularies to. Defaults to "turtle".

    """
    module = importlib.import_module(module)
    vocabs = vocabs_from_module(module)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for vocab in vocabs:
        v = vocab()
        destination = os.path.join(output_dir, v.name + "." + format)
        v.serialize(format=format, destination=destination)
