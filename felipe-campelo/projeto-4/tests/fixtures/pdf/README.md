# PDF Fixtures

This directory remains reserved for two real fixture PDFs in later validation:

- one tabular quarterly result document
- one slide-style quarterly result document

Current project status:

- the regression milestone is already covered by synthetic PDFs generated in tests
- the end-to-end audit trail for both layouts is asserted in `tests/integration/test_pipeline_two_layouts_audit.py`
- real market PDFs are still validated separately through `app.tools.validate_real_pdf`
