# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import re
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parents[2] / 'builder' / 'Dockerfile'


def _parse_instructions(dockerfile: Path, instruction: str):
    """Return a list of JSON-exec-form arg lists for the given Dockerfile instruction."""
    results = []
    pattern = re.compile(rf'^\s*{instruction}\s+\[(.+)\]\s*$', re.IGNORECASE)
    for line in dockerfile.read_text(encoding='utf-8').splitlines():
        m = pattern.match(line)
        if m:
            # Parse the JSON array manually: split by comma, strip quotes/whitespace
            raw = m.group(1)
            args = [s.strip().strip('"').strip("'") for s in raw.split(',')]
            results.append(args)
    return results


class TestDockerfileEntrypoint:
    """Guard against regressions where CMD or ENTRYPOINT pass bad args to the builder."""

    def test_entrypoint_is_builder_command(self):
        entries = _parse_instructions(DOCKERFILE, 'ENTRYPOINT')
        assert len(entries) == 1, 'Dockerfile should have exactly one ENTRYPOINT'
        assert entries[0] == ['az', 'bake', '_builder', 'build', '--verbose']

    def test_no_cmd_with_empty_args(self):
        """CMD with empty strings would be appended to ENTRYPOINT causing 'unrecognized arguments'."""
        cmds = _parse_instructions(DOCKERFILE, 'CMD')
        for cmd_args in cmds:
            for arg in cmd_args:
                assert arg.strip() != '', (
                    f'CMD must not contain empty-string arguments (found {cmd_args!r}). '
                    'Empty strings are appended to ENTRYPOINT and cause "unrecognized arguments" errors.'
                )
