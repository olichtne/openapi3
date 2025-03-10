"""
Tests parsing specs
"""
import pytest

from openapi3 import OpenAPI, SpecError, ReferenceResolutionError


def test_parse_from_yaml(petstore_expanded):
    """
    Tests that we can parse a valid yaml file
    """
    spec = OpenAPI(petstore_expanded)


def test_parsing_fails(broken):
    """
    Tests that broken specs fail to parse
    """
    with pytest.raises(
        SpecError, match=r"Expected .info to be of type Info, with required fields \['title', 'version'\]"
    ):
        spec = OpenAPI(broken)


def test_parsing_broken_refernece(broken_reference):
    """
    Tests that parsing fails correctly when a reference is broken
    """
    with pytest.raises(ReferenceResolutionError):
        spec = OpenAPI(broken_reference)


def test_parsing_wrong_parameter_name(has_bad_parameter_name):
    """
    Tests that parsing fails if parameter name for path parameters aren't
    actually in the path.
    """
    with pytest.raises(SpecError, match="Parameter name not found in path: different"):
        spec = OpenAPI(has_bad_parameter_name)


def test_parsing_dupe_operation_id(dupe_op_id):
    """
    Tests that duplicate operation Ids are an error
    """
    with pytest.raises(SpecError, match="Duplicate operationId dupe"):
        spec = OpenAPI(dupe_op_id)


def test_parsing_parameter_name_with_underscores(parameter_with_underscores):
    """
    Tests that path parameters with underscores in them are accepted
    """
    spec = OpenAPI(parameter_with_underscores)


def test_object_example(obj_example_expanded):
    """
    Tests that `example` exists.
    """
    spec = OpenAPI(obj_example_expanded)
    schema = spec.paths["/check-dict"].get.responses["200"].content["application/json"].schema
    assert isinstance(schema.example, dict)
    assert isinstance(schema.example["real"], float)

    schema = spec.paths["/check-str"].get.responses["200"].content["text/plain"]
    assert isinstance(schema.example, str)


def test_parsing_float_validation(float_validation_expanded):
    """
    Tests that `minimum` and similar validators work with floats.
    """
    spec = OpenAPI(float_validation_expanded)
    properties = spec.paths["/foo"].get.responses["200"].content["application/json"].schema.properties

    assert isinstance(properties["integer"].minimum, int)
    assert isinstance(properties["integer"].maximum, int)
    assert isinstance(properties["real"].minimum, float)
    assert isinstance(properties["real"].maximum, float)


def test_parsing_with_links(with_links):
    """
    Tests that "links" parses correctly
    """
    spec = OpenAPI(with_links)

    assert "exampleWithOperationRef" in spec.components.links
    assert spec.components.links["exampleWithOperationRef"].operationRef == "/with-links"

    response_a = spec.paths["/with-links"].get.responses["200"]
    assert "exampleWithOperationId" in response_a.links
    assert response_a.links["exampleWithOperationId"].operationId == "withLinksTwo"

    response_b = spec.paths["/with-links-two/{param}"].get.responses["200"]
    assert "exampleWithRef" in response_b.links
    assert response_b.links["exampleWithRef"] == spec.components.links["exampleWithOperationRef"]


def test_param_types(with_param_types):
    spec = OpenAPI(with_param_types, validate=True)

    errors = spec.errors()

    assert len(errors) == 0


def test_parsing_broken_links(with_broken_links):
    """
    Tests that broken "links" values error properly
    """
    spec = OpenAPI(with_broken_links, validate=True)

    errors = spec.errors()

    assert len(errors) == 2
    error_strs = [str(e) for e in errors]
    assert (
        sorted(
            [
                "operationId and operationRef are mutually exclusive, only one of them is allowed",
                "operationId and operationRef are mutually exclusive, one of them must be specified",
            ]
        )
        == sorted(error_strs)
    )


def test_securityparameters(with_securityparameters):
    spec = OpenAPI(with_securityparameters, validate=True)
    errors = spec.errors()
    assert len(errors) == 0


def test_example_type_array(with_array_example):
    """
    Tests that examples, definied as "any" type, accept arrays
    """
    spec = OpenAPI(with_array_example, validate=True)
    assert len(spec.errors()) == 0, spec.errors()
