# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

import os
import sys
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from azext_bake._ci import (
    BuildResult,
    LOG_TAIL_LINES,
    TERMINATED,
    _fetch_logs,
    _get_container_state,
    _stream_log_delta,
    _tail_lines,
    emit_github_annotation,
    follow_image_logs,
    is_github_actions,
    poll_build,
    report_results,
    wait_for_builds,
    write_github_output,
    write_github_summary,
)


# -------------------------------------------------------
# BuildResult
# -------------------------------------------------------

class TestBuildResult:
    def test_succeeded(self):
        r = BuildResult(image_name='img', state=TERMINATED, exit_code=0)
        assert r.succeeded is True
        assert r.failed is False

    def test_failed(self):
        r = BuildResult(image_name='img', state=TERMINATED, exit_code=1)
        assert r.succeeded is False
        assert r.failed is True

    def test_unknown(self):
        r = BuildResult(image_name='img', state='Running')
        assert r.succeeded is False
        assert r.failed is False

    def test_defaults(self):
        r = BuildResult(image_name='test')
        assert r.state == 'Unknown'
        assert r.exit_code is None
        assert r.portal_url == ''


# -------------------------------------------------------
# is_github_actions
# -------------------------------------------------------

class TestIsGitHubActions:
    def test_not_github(self, monkeypatch):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        monkeypatch.delenv('GITHUB_ACTION', raising=False)
        assert is_github_actions() is False

    def test_github_actions_env(self, monkeypatch):
        monkeypatch.setenv('GITHUB_ACTIONS', 'true')
        assert is_github_actions() is True

    def test_github_action_env(self, monkeypatch):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        monkeypatch.setenv('GITHUB_ACTION', 'run1')
        assert is_github_actions() is True


# -------------------------------------------------------
# emit_github_annotation
# -------------------------------------------------------

class TestEmitGitHubAnnotation:
    def test_error_with_title(self, capsys):
        emit_github_annotation('error', 'Build broke', title='img1 failed')
        out = capsys.readouterr().out
        assert out.startswith('::error title=img1 failed::Build broke')

    def test_warning_no_title(self, capsys):
        emit_github_annotation('warning', 'Something odd')
        out = capsys.readouterr().out
        assert out.startswith('::warning::Something odd')

    def test_notice(self, capsys):
        emit_github_annotation('notice', 'All good', title='success')
        out = capsys.readouterr().out
        assert '::notice title=success::All good' in out

    def test_newlines_encoded(self, capsys):
        emit_github_annotation('error', 'line1\nline2')
        out = capsys.readouterr().out
        assert '%0A' in out
        assert '\n' not in out.split('::error::')[1].rstrip('\n')


# -------------------------------------------------------
# write_github_output
# -------------------------------------------------------

class TestWriteGitHubOutput:
    def test_writes_key_value(self, tmp_path, monkeypatch):
        out_file = tmp_path / 'output.txt'
        monkeypatch.setenv('GITHUB_OUTPUT', str(out_file))
        write_github_output('build_result', 'success')
        assert out_file.read_text(encoding='utf-8') == 'build_result=success\n'

    def test_appends(self, tmp_path, monkeypatch):
        out_file = tmp_path / 'output.txt'
        monkeypatch.setenv('GITHUB_OUTPUT', str(out_file))
        write_github_output('key1', 'val1')
        write_github_output('key2', 'val2')
        content = out_file.read_text(encoding='utf-8')
        assert 'key1=val1\n' in content
        assert 'key2=val2\n' in content

    def test_no_env_no_error(self, monkeypatch):
        monkeypatch.delenv('GITHUB_OUTPUT', raising=False)
        write_github_output('key', 'val')  # should not raise


# -------------------------------------------------------
# write_github_summary
# -------------------------------------------------------

class TestWriteGitHubSummary:
    def test_writes_markdown(self, tmp_path, monkeypatch):
        summary_file = tmp_path / 'summary.md'
        monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(summary_file))
        write_github_summary('## Results\n| a | b |')
        content = summary_file.read_text(encoding='utf-8')
        assert '## Results' in content

    def test_no_env_no_error(self, monkeypatch):
        monkeypatch.delenv('GITHUB_STEP_SUMMARY', raising=False)
        write_github_summary('test')  # should not raise


# -------------------------------------------------------
# _tail_lines
# -------------------------------------------------------

class TestTailLines:
    def test_short_content(self):
        assert _tail_lines('line1\nline2') == 'line1\nline2'

    def test_exact_limit(self):
        lines = '\n'.join(f'line{i}' for i in range(LOG_TAIL_LINES))
        assert _tail_lines(lines) == lines

    def test_over_limit(self):
        lines = '\n'.join(f'line{i}' for i in range(LOG_TAIL_LINES + 20))
        result = _tail_lines(lines)
        result_lines = result.splitlines()
        assert len(result_lines) == LOG_TAIL_LINES
        assert result_lines[-1] == f'line{LOG_TAIL_LINES + 19}'

    def test_empty(self):
        assert _tail_lines('') == ''


# -------------------------------------------------------
# _stream_log_delta
# -------------------------------------------------------

class TestStreamLogDelta:
    def test_no_new_content(self, capsys):
        new_len = _stream_log_delta('img', 'hello', 5)
        assert new_len == 5
        assert capsys.readouterr().out == ''

    def test_new_content(self, capsys):
        new_len = _stream_log_delta('img', 'hello world', 6)
        assert new_len == 11
        assert 'world' in capsys.readouterr().out

    def test_first_content(self, capsys):
        new_len = _stream_log_delta('img', 'first log', 0)
        assert new_len == 9
        assert 'first log' in capsys.readouterr().out

    def test_with_groups(self, capsys):
        _stream_log_delta('img', 'hello world', 6, use_groups=True)
        out = capsys.readouterr().out
        assert '::group::img' in out
        assert '::endgroup::' in out
        assert 'world' in out


# -------------------------------------------------------
# _get_container_state
# -------------------------------------------------------

class TestGetContainerState:
    def test_no_containers(self):
        cg = MagicMock()
        cg.containers = []
        state, exit_code, detail = _get_container_state(cg)
        assert state is None

    def test_no_instance_view(self):
        container = MagicMock()
        container.instance_view = None
        cg = MagicMock()
        cg.containers = [container]
        cg.provisioning_state = 'Creating'
        state, exit_code, detail = _get_container_state(cg)
        assert state == 'Creating'
        assert exit_code is None

    def test_running(self):
        current = MagicMock()
        current.state = 'Running'
        current.exit_code = None
        current.detail_status = ''
        container = MagicMock()
        container.instance_view = MagicMock()
        container.instance_view.current_state = current
        cg = MagicMock()
        cg.containers = [container]
        state, exit_code, detail = _get_container_state(cg)
        assert state == 'Running'

    def test_terminated_success(self):
        current = MagicMock()
        current.state = TERMINATED
        current.exit_code = 0
        current.detail_status = 'Completed'
        container = MagicMock()
        container.instance_view = MagicMock()
        container.instance_view.current_state = current
        cg = MagicMock()
        cg.containers = [container]
        state, exit_code, detail = _get_container_state(cg)
        assert state == TERMINATED
        assert exit_code == 0
        assert detail == 'Completed'

    def test_terminated_failure(self):
        current = MagicMock()
        current.state = TERMINATED
        current.exit_code = 1
        current.detail_status = 'Error'
        container = MagicMock()
        container.instance_view = MagicMock()
        container.instance_view.current_state = current
        cg = MagicMock()
        cg.containers = [container]
        state, exit_code, detail = _get_container_state(cg)
        assert state == TERMINATED
        assert exit_code == 1


# -------------------------------------------------------
# poll_build
# -------------------------------------------------------

class TestPollBuild:
    @patch('azext_bake._ci.cf_container')
    @patch('azext_bake._ci.cf_container_groups')
    def test_running_container(self, mock_cg_factory, mock_c_factory):
        # Setup container group mock
        current_state = MagicMock()
        current_state.state = 'Running'
        current_state.exit_code = None
        current_state.detail_status = ''
        current_state.start_time = '2026-01-01T00:00:00Z'
        current_state.finish_time = None

        container = MagicMock()
        container.name = 'builder'
        container.instance_view = MagicMock()
        container.instance_view.current_state = current_state

        cg = MagicMock()
        cg.containers = [container]
        cg.provisioning_state = 'Succeeded'

        mock_cg_factory.return_value.get.return_value = cg

        # Setup log mock
        log_mock = MagicMock()
        log_mock.content = 'Building image...'
        mock_c_factory.return_value.list_logs.return_value = log_mock

        cli_ctx = MagicMock()
        result, logs = poll_build(cli_ctx, 'my-rg', 'TestImage')

        assert result.image_name == 'TestImage'
        assert result.state == 'Running'
        assert result.exit_code is None
        assert 'Building image...' in logs

    @patch('azext_bake._ci.cf_container')
    @patch('azext_bake._ci.cf_container_groups')
    def test_terminated_container(self, mock_cg_factory, mock_c_factory):
        current_state = MagicMock()
        current_state.state = TERMINATED
        current_state.exit_code = 0
        current_state.detail_status = 'Completed'
        current_state.start_time = '2026-01-01T00:00:00Z'
        current_state.finish_time = '2026-01-01T00:15:00Z'

        container = MagicMock()
        container.name = 'builder'
        container.instance_view = MagicMock()
        container.instance_view.current_state = current_state

        cg = MagicMock()
        cg.containers = [container]
        cg.provisioning_state = 'Succeeded'

        mock_cg_factory.return_value.get.return_value = cg

        log_mock = MagicMock()
        log_mock.content = 'Done!'
        mock_c_factory.return_value.list_logs.return_value = log_mock

        cli_ctx = MagicMock()
        result, logs = poll_build(cli_ctx, 'my-rg', 'TestImage')

        assert result.state == TERMINATED
        assert result.exit_code == 0
        assert result.succeeded is True


# -------------------------------------------------------
# report_results
# -------------------------------------------------------

class TestReportResults:
    def test_all_succeeded(self, monkeypatch):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        monkeypatch.delenv('GITHUB_ACTION', raising=False)
        results = [
            BuildResult('img1', TERMINATED, exit_code=0),
            BuildResult('img2', TERMINATED, exit_code=0),
        ]
        failed = report_results(results)
        assert failed == []

    def test_some_failed(self, monkeypatch):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        monkeypatch.delenv('GITHUB_ACTION', raising=False)
        results = [
            BuildResult('img1', TERMINATED, exit_code=0),
            BuildResult('img2', TERMINATED, exit_code=1, logs_tail='error log'),
        ]
        failed = report_results(results)
        assert len(failed) == 1
        assert failed[0].image_name == 'img2'

    def test_github_annotations_on_failure(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv('GITHUB_ACTIONS', 'true')
        summary_file = tmp_path / 'summary.md'
        output_file = tmp_path / 'output.txt'
        monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(summary_file))
        monkeypatch.setenv('GITHUB_OUTPUT', str(output_file))

        results = [
            BuildResult('good', TERMINATED, exit_code=0),
            BuildResult('bad', TERMINATED, exit_code=1, logs_tail='packer error'),
        ]
        report_results(results)

        out = capsys.readouterr().out
        # Error annotation for failed build
        assert '::error' in out
        assert 'bad build failed' in out
        # Notice annotation for success
        assert '::notice' in out
        assert 'good build succeeded' in out

        # Step summary written
        summary = summary_file.read_text(encoding='utf-8')
        assert 'Build Results' in summary
        assert ':x: Failed' in summary
        assert ':white_check_mark: Succeeded' in summary
        assert 'packer error' in summary

        # GITHUB_OUTPUT written
        gh_output = output_file.read_text(encoding='utf-8')
        assert 'build_result=failure' in gh_output
        assert 'failed_images=bad' in gh_output
        assert 'succeeded_images=good' in gh_output

    def test_github_all_success(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv('GITHUB_ACTIONS', 'true')
        summary_file = tmp_path / 'summary.md'
        output_file = tmp_path / 'output.txt'
        monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(summary_file))
        monkeypatch.setenv('GITHUB_OUTPUT', str(output_file))

        results = [BuildResult('img1', TERMINATED, exit_code=0)]
        failed = report_results(results)

        assert failed == []
        gh_output = output_file.read_text(encoding='utf-8')
        assert 'build_result=success' in gh_output


# -------------------------------------------------------
# wait_for_builds (with mocked poll_build)
# -------------------------------------------------------

class TestWaitForBuilds:
    @patch('azext_bake._ci.POLL_INTERVAL_SECONDS', 0)
    @patch('azext_bake._ci.poll_build')
    def test_immediate_completion(self, mock_poll, monkeypatch):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        monkeypatch.delenv('GITHUB_ACTION', raising=False)

        result = BuildResult('img1', TERMINATED, exit_code=0, logs_tail='done')
        mock_poll.return_value = (result, 'full log content')

        cmd = MagicMock()
        results = wait_for_builds(cmd, 'my-rg', ['img1'])

        assert len(results) == 1
        assert results[0].succeeded is True

    @patch('azext_bake._ci.POLL_INTERVAL_SECONDS', 0)
    @patch('azext_bake._ci.poll_build')
    def test_multiple_images(self, mock_poll, monkeypatch):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        monkeypatch.delenv('GITHUB_ACTION', raising=False)

        r1 = BuildResult('img1', TERMINATED, exit_code=0)
        r2 = BuildResult('img2', TERMINATED, exit_code=1, logs_tail='error')
        mock_poll.side_effect = [
            (r1, 'log1'), (r2, 'log2'),
        ]

        cmd = MagicMock()
        results = wait_for_builds(cmd, 'my-rg', ['img1', 'img2'])

        assert len(results) == 2
        assert results[0].image_name == 'img1'
        assert results[1].image_name == 'img2'

    @patch('azext_bake._ci.POLL_INTERVAL_SECONDS', 0)
    @patch('azext_bake._ci.poll_build')
    def test_polls_until_terminated(self, mock_poll, monkeypatch):
        """Container is Running on first poll, Terminated on second."""
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
        monkeypatch.delenv('GITHUB_ACTION', raising=False)

        running = BuildResult('img1', 'Running')
        terminated = BuildResult('img1', TERMINATED, exit_code=0)
        mock_poll.side_effect = [
            (running, 'partial log'),
            (terminated, 'full log'),
        ]

        cmd = MagicMock()
        results = wait_for_builds(cmd, 'my-rg', ['img1'])

        assert len(results) == 1
        assert results[0].state == TERMINATED
        assert mock_poll.call_count == 2


# -------------------------------------------------------
# follow_image_logs (with mocked clients)
# -------------------------------------------------------

class TestFollowImageLogs:
    @patch('azext_bake._ci.POLL_INTERVAL_SECONDS', 0)
    @patch('azext_bake._ci._fetch_logs')
    @patch('azext_bake._ci.cf_container_groups')
    def test_follows_until_terminated(self, mock_cg_factory, mock_fetch, monkeypatch, capsys):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)

        # First call: running
        running_state = MagicMock()
        running_state.state = 'Running'
        running_state.exit_code = None
        running_state.detail_status = ''
        running_container = MagicMock()
        running_container.name = 'builder'
        running_container.instance_view = MagicMock()
        running_container.instance_view.current_state = running_state
        running_cg = MagicMock()
        running_cg.containers = [running_container]

        # Second call: terminated
        term_state = MagicMock()
        term_state.state = TERMINATED
        term_state.exit_code = 0
        term_state.detail_status = 'Completed'
        term_container = MagicMock()
        term_container.name = 'builder'
        term_container.instance_view = MagicMock()
        term_container.instance_view.current_state = term_state
        term_cg = MagicMock()
        term_cg.containers = [term_container]

        mock_cg_factory.return_value.get.side_effect = [running_cg, term_cg]
        mock_fetch.side_effect = ['Building...', 'Building...\nDone!']

        cmd = MagicMock()
        exit_code = follow_image_logs(cmd, 'my-rg', 'TestImage')

        assert exit_code == 0
        out = capsys.readouterr().out
        assert 'Building...' in out

    @patch('azext_bake._ci.POLL_INTERVAL_SECONDS', 0)
    @patch('azext_bake._ci._fetch_logs')
    @patch('azext_bake._ci.cf_container_groups')
    def test_returns_nonzero_on_failure(self, mock_cg_factory, mock_fetch, monkeypatch):
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)

        term_state = MagicMock()
        term_state.state = TERMINATED
        term_state.exit_code = 2
        term_state.detail_status = 'Error'
        container = MagicMock()
        container.name = 'builder'
        container.instance_view = MagicMock()
        container.instance_view.current_state = term_state
        cg = MagicMock()
        cg.containers = [container]

        mock_cg_factory.return_value.get.return_value = cg
        mock_fetch.return_value = 'error log'

        cmd = MagicMock()
        exit_code = follow_image_logs(cmd, 'my-rg', 'TestImage')

        assert exit_code == 2
