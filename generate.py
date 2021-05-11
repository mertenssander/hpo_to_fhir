from pronto import Ontology
from fhir.resources import codesystem
import logging, json, tqdm

'''
Transformation of HPO to FHIR
Created by https://github.com/mertenssander/

Depends on modules:
- fhir.resources module https://github.com/nazrulworld/fhir.resources
- pronto https://pronto.readthedocs.io/en/stable/api.html
- logging, json, tqdm

This transformation includes EXACT synonyms as synonymous designations.
Xrefs are included as a property
Subsets are included as a property
'''

def generate_codesystem():
    # Settings
    filename                = "hp.owl"
    url                     = "https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.owl"
    codesystem_url          = "http://purl.obolibrary.org/obo/hp.owl"
    codesystem_experimental = True
    download                = True
    filename_output         = "hp.owl.json"

    # Initialize logger and start generating resource
    logging.basicConfig(
        format='[%(levelname)8s] %(asctime)s | [%(module)20.20s] | %(message)s', 
        datefmt='%m/%d/%Y %I:%M:%S %p', level = logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Setup logger")
    logger.info(f"Loglevel: {logging.getLevelName(logger.getEffectiveLevel())}")

    # Load ontology
    logger.info("Inladen HPO gestart")
    if download:
        logger.info("Download bronbestand")
        hpo = Ontology(url)
    else:
        logger.info("Inladen van harde schijf")
        hpo = Ontology.from_obo_library(filename)
    logger.info("Inladen HPO voltooid")

    # Initialize CodeSystem class
    stelsel = codesystem.CodeSystem(**{
        "status"    : "active",
        "content"   : "complete"
    } )
    stelsel.version         = f"http://purl.obolibrary.org/obo/hp/{hpo.metadata.data_version}/hp.owl"
    stelsel.name            = 'HPO'
    stelsel.title           = 'Human Phenotype Ontology'
    stelsel.versionNeeded   = False
    stelsel.experimental    = codesystem_experimental
    stelsel.url             = codesystem_url
    stelsel.valueSet        = codesystem_url+'?vs'
    stelsel.count           = int(len(hpo.terms()))
    stelsel.copyright       = "Please see license of HPO at http://www.human-phenotype-ontology.org."
    stelsel.purpose         = "To provide a standardized vocabulary of human phenotypes encountered in human disease in a FHIR context."
    stelsel.date            = hpo.metadata.data_version.split("/")[-1]
    stelsel.concept         = list()

    # Output some debug data about the CodeSystem
    logger.info(f"URI:\t\t{stelsel.url}")
    logger.info(f"Version:\t\t{stelsel.version}")
    logger.info(f"Concept count:\t{stelsel.count}")

    # Start adding concepts to the CodeSystem
    logger.info("Concepten toevoegen aan CodeSystem")
    for concept in tqdm.tqdm(hpo.terms()):
        ### Code en display ###
        #region
        _concept = codesystem.CodeSystemConcept(**{
            'code'      : str(concept.id),
            'display'   : str(concept.name),
        })
        #endregion

        # Designations
        #region
        _designations = []
        for synonym in concept.synonyms:
            if synonym.scope == 'EXACT':
                _designations.append(codesystem.CodeSystemConceptDesignation(**{
                    'language' : 'en',
                    'value' : str(synonym.description),
                    'use' : {
                        "system": "http://snomed.info/sct",
                        "code": "900000000000013009",
                        "display": "Synonym"
                    }
                }))
            else:
                logger.debug(f"Skip designation {synonym} for {concept.id} - scope == {synonym.scope}")
        if len(_designations) > 0:
            _concept.designation = _designations        
        #endregion

        # Properties
        #region
        _properties = []
        
        ## Active
        _properties.append(codesystem.CodeSystemConceptProperty(**{
            'code' : 'inactive',
            'valueBoolean' : concept.obsolete
        }))

        ## Definition
        if concept.definition:
            _properties.append(codesystem.CodeSystemConceptProperty(**{
                'code' : 'definition',
                'valueString' : concept.definition
            }))

        ## Xrefs
        for xref in concept.xrefs:
            _properties.append(codesystem.CodeSystemConceptProperty(**{
                'code' : 'xref',
                'valueString' : str(xref.id)
            }))

        ## Superclasses
        for superclass in concept.superclasses(with_self=False, distance=1).to_set():
            _properties.append(codesystem.CodeSystemConceptProperty(**{
                'code' : 'parent',
                'valueCode' : str(superclass.id)
            }))

        ## Subclasses
        for subclass in concept.subclasses(with_self=False, distance=1).to_set():
            _properties.append(codesystem.CodeSystemConceptProperty(**{
                'code' : 'child',
                'valueCode' : str(subclass.id)
            }))

        ## Subsets
        for subset in concept.subsets:
            _properties.append(codesystem.CodeSystemConceptProperty(**{
                'code' : 'subset',
                'valueString' : str(subset)
            }))

        if len(_properties) > 0:
            _concept.property = _properties
        #endregion
        
        # Add concept to CodeSystem
        logger.debug(f"Concept {concept.id} toegevoegd aan CodeSystem.")
        stelsel.concept.append(_concept)

    # Write to file
    logger.info(f"{len(stelsel.concept)} concepten toegevoegd aan het CodeSystem. Exporteren naar JSON.")
    logger.info("Voltooid - schrijf CodeSystem naar bestand")
    with open(filename_output, 'w') as outfile:
        outfile.write(json.dumps(stelsel.dict(),indent=2,default=str, ensure_ascii=False))
    logger.info(f"CodeSystem geschreven naar {filename_output}.")

if __name__ == '__main__':
    generate_codesystem()
