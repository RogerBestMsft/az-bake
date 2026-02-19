# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
# pylint: disable=logging-fstring-interpolation

import os
import sys
import time

from dataclasses import dataclass
from typing import Optional

from ._client_factory import cf_container, cf_container_groups
from ._utils import get_logger

logger = get_logger(__name__)

POLL_INTERVAL_SECONDS = 15
TERMINATED = 'Terminated'
LOG_TAIL_LINES = 50


@dataclass
class BuildResult:  # pylint: disable=too-many-instance-attributes
    """Result of a single container instance build."""
    image_name: str
    state: str = 'Unknown'
    exit_code: Optional[int] = None
    start_time: Optional[str] = None
    finish_time: Optional[str] = None
    detail_status: str = ''
    logs_tail: str = ''
    portal_url: str = ''

    @property
    def succeeded(self):
        return self.exit_code == 0

    @property
    def failed(self):
        return self.exit_code is not None and self.exit_code != 0


def is_github_actions():
    """Check if running inside GitHub Actions."""
    return bool(os.environ.get('GITHUB_ACTIONS') or os.environ.get('GITHUB_ACTION'))


def emit_github_annotation(level, message, title=None):
    """Emit a GitHub Actions annotation (error, warning, notice).

    See https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions
    """
    title_part = f' title={title}' if title else ''
    # GitHub annotations must be on a single line; replace newlines for the message
    safe_msg = message.replace('\n', '%0A')
    print(f'::{level}{title_part}::{safe_msg}', flush=True)


def write_github_output(key, value):
    """Append a key=value pair to $GITHUB_OUTPUT for downstream steps."""
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f'{key}={value}\n')


def write_github_summary(markdown):
    """Append markdown content to $GITHUB_STEP_SUMMARY."""
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(markdown + '\n')


def _get_container_state(container_group):
    """Extract the current state from the first container in a container group."""
    containers = container_group.containers or []
    if not containers:
        return None, None, None

    instance_view = containers[0].instance_view
    if not instance_view or not instance_view.current_state:
        return container_group.provisioning_state, None, None

    current = instance_view.current_state
    return current.state, getattr(current, 'exit_code', None), current.detail_status


def _fetch_logs(cli_ctx, resource_group, container_group_name, container_name):
    """Fetch the full log content from a container."""
    try:
        container_client = cf_container(cli_ctx)
        log = container_client.list_logs(resource_group, container_group_name, container_name)
        return log.content or ''
    except Exception:  # pylint: disable=broad-except
        return ''


def _stream_log_delta(image_name, full_content, previous_length, use_groups=False):
    """Print only the new portion of logs since last check.

    Returns the new total length for tracking.
    """
    if len(full_content) <= previous_length:
        return previous_length

    delta = full_content[previous_length:]
    if use_groups:
        print(f'::group::{image_name} (log update)', flush=True)

    sys.stdout.write(delta)
    sys.stdout.flush()

    if use_groups:
        print('::endgroup::', flush=True)

    return len(full_content)


def _tail_lines(content, n=LOG_TAIL_LINES):
    """Return the last n lines of content."""
    lines = content.strip().splitlines()
    return '\n'.join(lines[-n:])


def poll_build(cli_ctx, resource_group, image_name):
    """Poll a single container group and return its current BuildResult."""
    container_group_client = cf_container_groups(cli_ctx)
    cg = container_group_client.get(resource_group, image_name)

    state, exit_code, detail_status = _get_container_state(cg)

    container_name = cg.containers[0].name if cg.containers else image_name
    logs = _fetch_logs(cli_ctx, resource_group, image_name, container_name)

    result = BuildResult(
        image_name=image_name,
        state=state or cg.provisioning_state or 'Unknown',
        exit_code=exit_code,
        detail_status=detail_status or '',
        logs_tail=_tail_lines(logs),
    )

    instance_view = cg.containers[0].instance_view if cg.containers else None
    if instance_view and instance_view.current_state:
        cs = instance_view.current_state
        result.start_time = str(cs.start_time) if cs.start_time else None
        result.finish_time = str(cs.finish_time) if cs.finish_time else None

    return result, logs


def wait_for_builds(cmd, resource_group, image_names, portal_urls=None):
    """Wait for all container instance builds to complete.

    Polls every POLL_INTERVAL_SECONDS, streaming logs incrementally.
    Returns a list of BuildResult objects.
    """
    if portal_urls is None:
        portal_urls = {}

    in_github = is_github_actions()
    cli_ctx = cmd.cli_ctx

    # Track log offsets per image for incremental streaming
    log_offsets = {name: 0 for name in image_names}
    completed = set()
    results = {}

    logger.warning('Waiting for builds to complete...')
    if in_github:
        print('::group::Build progress', flush=True)

    while len(completed) < len(image_names):
        for name in image_names:
            if name in completed:
                continue

            try:
                result, full_logs = poll_build(cli_ctx, resource_group, name)
            except Exception as ex:  # pylint: disable=broad-except
                logger.info(f'Error polling {name}: {ex}')
                continue

            result.portal_url = portal_urls.get(name, '')
            results[name] = result

            # Stream incremental logs
            log_offsets[name] = _stream_log_delta(
                name, full_logs, log_offsets[name],
                use_groups=(in_github and len(image_names) > 1)
            )

            # Check if terminated
            if result.state == TERMINATED:
                completed.add(name)
                status_str = 'succeeded' if result.succeeded else f'FAILED (exit code {result.exit_code})'
                logger.warning(f'{name}: build {status_str}')

        if len(completed) < len(image_names):
            pending = [n for n in image_names if n not in completed]
            logger.info(f'Waiting for {len(pending)} build(s): {", ".join(pending)}')
            time.sleep(POLL_INTERVAL_SECONDS)

    if in_github:
        print('::endgroup::', flush=True)

    return [results[name] for name in image_names]


def report_results(results, repo=None):  # pylint: disable=unused-argument
    """Report build results to GitHub Actions (annotations, summary, output).

    Also prints a summary table to the console.
    """
    in_github = is_github_actions()

    failed = [r for r in results if r.failed]
    succeeded = [r for r in results if r.succeeded]

    # Console summary
    logger.warning('')
    logger.warning('=' * 60)
    logger.warning('BUILD RESULTS')
    logger.warning('=' * 60)
    for r in results:
        icon = '✓' if r.succeeded else ('✗' if r.failed else '?')
        code_str = f' (exit code {r.exit_code})' if r.exit_code is not None else ''
        logger.warning(f'  {icon} {r.image_name}: {r.state}{code_str}')
    logger.warning('=' * 60)

    if in_github:
        # Error annotations for failures
        for r in failed:
            tail = r.logs_tail or '(no logs available)'
            emit_github_annotation(
                'error',
                f'Build failed with exit code {r.exit_code}.\n\nLast {LOG_TAIL_LINES} lines:\n{tail}',
                title=f'{r.image_name} build failed'
            )

        # Notice annotations for successes
        for r in succeeded:
            emit_github_annotation(
                'notice',
                'Build completed successfully.',
                title=f'{r.image_name} build succeeded'
            )

        # Step summary
        summary_lines = [
            '## Build Results\n',
            '| Image | Status | Exit Code | Details |',
            '|-------|--------|-----------|---------|',
        ]
        for r in results:
            if r.succeeded:
                status = ':white_check_mark: Succeeded'
            elif r.failed:
                status = ':x: Failed'
            else:
                status = ':grey_question: Unknown'
            code = str(r.exit_code) if r.exit_code is not None else '-'
            portal = f'[Portal]({r.portal_url})' if r.portal_url else '-'
            summary_lines.append(f'| {r.image_name} | {status} | {code} | {portal} |')
        summary_lines.append('')

        if failed:
            summary_lines.append('### Failure Logs\n')
            for r in failed:
                summary_lines.append(f'<details><summary>{r.image_name}</summary>\n')
                summary_lines.append(f'```\n{r.logs_tail}\n```\n')
                summary_lines.append('</details>\n')

        write_github_summary('\n'.join(summary_lines))

        # GITHUB_OUTPUT for downstream steps
        build_result = 'failure' if failed else ('success' if succeeded else 'unknown')
        write_github_output('build_result', build_result)
        if failed:
            write_github_output('failed_images', ','.join(r.image_name for r in failed))
        if succeeded:
            write_github_output('succeeded_images', ','.join(r.image_name for r in succeeded))

    return failed


def follow_image_logs(cmd, resource_group, image_name):
    """Stream logs for a single image build until the container terminates."""
    cli_ctx = cmd.cli_ctx
    container_group_client = cf_container_groups(cli_ctx)

    log_offset = 0

    logger.warning(f'Following logs for {image_name}...')

    while True:
        try:
            cg = container_group_client.get(resource_group, image_name)
            state, exit_code, detail = _get_container_state(cg)

            container_name = cg.containers[0].name if cg.containers else image_name
            full_logs = _fetch_logs(cli_ctx, resource_group, image_name, container_name)

            log_offset = _stream_log_delta(image_name, full_logs, log_offset, use_groups=False)

            if state == TERMINATED:
                logger.warning('')
                if exit_code == 0:
                    logger.warning(f'{image_name}: build succeeded')
                else:
                    logger.warning(f'{image_name}: build FAILED (exit code {exit_code})')
                if detail:
                    logger.warning(f'  Detail: {detail}')
                return exit_code or 0

        except Exception as ex:  # pylint: disable=broad-except
            logger.info(f'Error polling {image_name}: {ex}')

        time.sleep(POLL_INTERVAL_SECONDS)
