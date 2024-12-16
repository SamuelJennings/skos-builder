import importlib
import logging
from pathlib import Path
from urllib.error import HTTPError

from rdflib import Graph

from .core import VocabularyBase
from .utils import LocalFilePathError, RemoteURLError, cache

logger = logging.getLogger(__name__)


class LocalVocabulary(VocabularyBase):
    """Base class for all ConceptSchemes. This class should not be used directly with a ConceptField. Instead, use a subclass that points towards a source file.

    Example:

    .. code-block:: python

            from research_vocabs import LocalVocabulary

            class SimpleLithology(ConceptScheme):
                # locally stored file (path is relative to the class file)
                source = "./vocabs/simple_lithology.ttl"

                # remote file
                source = "https://vocabs.ardc.edu.au/registry/api/resource/downloads/1211/isc2020.ttl"


    """

    def build_graph(self):
        # get file path of class
        calling_module = importlib.import_module(self.__class__.__module__)
        source_kwargs = self._source()

        source_kwargs["source"] = (
            Path(calling_module.__file__).parent / source_kwargs["source"]
        ).resolve()

        if not source_kwargs["source"].exists():
            raise LocalFilePathError(self.__class__.__name__)

        return Graph().parse(**source_kwargs)


class RemoteVocabulary(LocalVocabulary):
    """A subclass of LocalVocabulary that is specifically for remote sources. The graph is cached for performance.

    Example:

    .. code-block:: python

        from research_vocabs import RemoteVocabulary

        class SimpleLithology(RemoteVocabulary):
            source = "https://vocabs.ardc.edu.au/registry/api/resource/downloads/1211/isc2020.ttl"

    """

    def build_graph(self):
        source_kwargs = self._source()

        # check if graph is in cache
        if graph := cache.get(source_kwargs["source"]):
            return graph
        try:
            graph = Graph().parse(**source_kwargs)
        except HTTPError as e:
            raise RemoteURLError(
                self.__class__.__name__, source_kwargs["source"]
            ) from e
        else:
            cache.set(source_kwargs["source"], graph, None)
            return graph
