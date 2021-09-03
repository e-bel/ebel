"""ClinicalTrials API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS


class TestClinicalTrials:
    def test_get_ct_by_nct_id(self, client):
        response = client.get(
            'api/v1/clinical_trial/by_nct_id?nct_id=NCT00571064',
            content_type='application/json'
        )

        output = format_response_data(response)
        expected_results = {
          "brief_summary": "This is a study to determine the effectiveness and safety of donepezil hydrochloride (E2020) used to treat residents of assisted living facilities diagnosed with mild, moderate, or severe stage Alzheimer's disease.",
          "brief_title": "The Effectiveness And Safety Of Donepezil Hydrochloride (E2020) In Subjects With Mild To Severe Alzheimer's Disease Residing In An Assisted Living Facility",
          "completion_date": "April 22, 2009",
          "conditions": [
            "Mild to Severe Alzheimer's Disease"
          ],
          "detailed_description": None,
          "id": 47330,
          "interventions": [
            {
              "intervention_name": "Donepezil HCl",
              "intervention_type": "Drug"
            }
          ],
          "is_fda_regulated_drug": None,
          "keywords": [],
          "mesh_terms": [
            "Alzheimer Disease"
          ],
          "nct_id": "NCT00571064",
          "official_title": "A 12-Week, Multicenter, Open Label Study To Evaluate The Effectiveness And Safety Of Donepezil Hydrochloride (E2020) In Subjects With Mild To Severe Alzheimer's Disease Residing In An Assisted Living Facility",
          "org_study_id": "E2020-A001-415",
          "overall_status": "Completed",
          "patient_data_ipd_description": None,
          "patient_data_sharing_ipd": None,
          "phase": "Phase 4",
          "start_date": "January 2008",
          "study_design_intervention_model": "Single Group Assignment",
          "study_design_masking": "None (Open Label)",
          "study_design_primary_purpose": "Treatment",
          "study_type": "Interventional"
        }

        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_ct_by_mesh_term(self, client):
        response = client.get(
            'api/v1/clinical_trial/by_mesh_term?mesh_term=Alzheimer%20Disease&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)

        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit["mesh_term"] == "Alzheimer Disease"
        assert len(hit["nct_ids"]) > 10
        assert "NCT00000171" in hit["nct_ids"]

    def test_get_ct_by_intervention(self, client):
        response = client.get(
            'api/v1/clinical_trial/by_intervention?intervention_name=Donepezil&intervention_type=Drug&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)

        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]

        assert isinstance(hit, dict)
        assert hit["intervention_name"] == "Donepezil"
        assert hit["intervention_type"] == "Drug"
        assert len(hit["nct_ids"]) >= 10
        assert "NCT00000173" in hit["nct_ids"]

    def test_get_ct_by_keyword(self, client):
        response = client.get(
            'api/v1/clinical_trial/by_keyword?keyword=Early%20Alzheimer&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)
        expected_results = {
          "keyword": "Early Alzheimer",
          "nct_ids": [
            "NCT01439555"
          ]
        }

        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_ct_by_condition(self, client):
        response = client.get(
            'api/v1/clinical_trial/by_condition?condition=Mild%20to%20Severe%20Alzheimer%27s%20Disease&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)
        expected_results = {
          "condition": "Mild to Severe Alzheimer's Disease",
          "nct_ids": [
            "NCT00571064"
          ]
        }

        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_mesh_term_starts_with(self, client):
        response = client.get(
            'api/v1/clinical_trial/mesh_term/starts_with?mesh_term=alz&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)

        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert "Alzheimer Disease" in results
        assert results["Alzheimer Disease"] > 3000

    def test_get_keyword_starts_with(self, client):
        response = client.get(
            'api/v1/clinical_trial/keyword/starts_with?keyword=alz&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)

        assert output[NUM_RESULTS] >= 9
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert "alzheimer's disease" in results
        assert results["alzheimer's disease"] > 4300

    def test_get_condition_starts_with(self, client):
        response = client.get(
            'api/v1/clinical_trial/condition/starts_with?condition=alz&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)

        assert output[NUM_RESULTS] > 70
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert "Alzheimer Disease 10" in results
        assert results["Alzheimer Disease 10"] > 5990
