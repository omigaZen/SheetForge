# TSV to Python Runtime Cases

This directory covers one end-to-end flow:

1. Edit a `tsv` source file
2. Run the generator and produce Python config classes plus binary data
3. Load the binary data through the Python runtime
4. Verify the loaded data matches the latest TSV edits

The repository does not contain the implementation yet, so this directory
stores a document-driven integration test skeleton and sample input data first.

## Contents

- `input/tb_item.tsv`
  - Sample TSV input
- `test_tsv_to_python_runtime.py`
  - End-to-end test cases

## Source Docs

- `docs/requirements.md`
- `docs/design.md`

## What These Tests Check

- The generator accepts `tsv` input
- Python class files `tb_item.py` and `tb_item_table.py` are emitted
- Binary data file `tb_item.sfc` is emitted
- The Python runtime supports `TbItemTable.load_from(...)`
- The runtime can read the latest edited row data, support lookup by id, and iterate rows
