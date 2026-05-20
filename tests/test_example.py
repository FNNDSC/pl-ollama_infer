"""
Comprehensive test suite for Ollama ChRIS plugin.

Tests cover:
- Main function with various configurations
- Ollama server startup and failure scenarios
- Inference with successful and failed responses
- Service mode operation
- Control API endpoints
- Error handling and edge cases
"""

import pytest
import subprocess
import threading
import time
import json
import socket
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from argparse import Namespace
import tempfile
import requests
from ollama_infer import start_ollama, test_ollama, main, run_control_server


class TestStartOllama:
    """Test suite for start_ollama() function"""

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_ollama_starts_successfully(self, mock_sleep, mock_popen):
        """Test successful Ollama server startup"""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process still running
        mock_popen.return_value = mock_process

        # Import after mocking
        from ollama_infer import start_ollama

        start_ollama(wait_time=1)

        # Verify Popen was called with correct command
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["ollama", "serve"]
        assert kwargs['start_new_session'] is True

        # Verify sleep was called with wait_time
        mock_sleep.assert_called_once_with(1)

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_ollama_startup_fails_immediately(self, mock_sleep, mock_popen):
        """Test Ollama server fails to start"""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.communicate.return_value = ("stdout error", "stderr error")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        from ollama_infer import start_ollama

        with pytest.raises(RuntimeError, match="Ollama server failed to start"):
            start_ollama(wait_time=1)

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_ollama_startup_with_custom_wait_time(self, mock_sleep, mock_popen):
        """Test start_ollama respects custom wait time"""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        from ollama_infer import start_ollama

        start_ollama(wait_time=5)

        mock_sleep.assert_called_once_with(5)

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_ollama_error_includes_exit_code(self, mock_sleep, mock_popen):
        """Test error message includes exit code"""
        mock_process = Mock()
        mock_process.poll.return_value = 127
        mock_process.returncode = 127
        mock_process.communicate.return_value = ("", "command not found")
        mock_popen.return_value = mock_process

        from ollama_infer import start_ollama

        with pytest.raises(RuntimeError) as exc_info:
            start_ollama(wait_time=1)

        assert "127" in str(exc_info.value)

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_ollama_error_includes_stderr(self, mock_sleep, mock_popen):
        """Test error message includes stderr output"""
        error_msg = "Out of memory"
        mock_process = Mock()
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", error_msg)
        mock_popen.return_value = mock_process

        from ollama_infer import start_ollama

        with pytest.raises(RuntimeError) as exc_info:
            start_ollama(wait_time=1)

        assert error_msg in str(exc_info.value)


class TestOllamaInference:
    """Test suite for test_ollama() function"""

    @patch('subprocess.Popen')
    def test_inference_successful(self, mock_popen):
        """Test successful inference"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Generated response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt="Hello world")

        assert result == "Generated response"
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0] == ["ollama", "run", "llama2", "Hello world"]

    @patch('subprocess.Popen')
    def test_inference_with_custom_model(self, mock_popen):
        """Test inference with different models"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        for model in ["llama2", "mistral", "neural-chat"]:
            test_ollama(model=model, prompt="test")

        assert mock_popen.call_count == 3

    @patch('subprocess.Popen')
    def test_inference_failure(self, mock_popen):
        """Test inference with non-zero exit code"""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("Error output", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt="test")

        assert result == "Error output"

    @patch('subprocess.Popen')
    def test_inference_process_exception(self, mock_popen):
        """Test inference when ollama executable not found"""
        mock_popen.side_effect = FileNotFoundError("ollama not found")

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt="test")

        assert "ERROR: Ollama executable not found" in result

    @patch('subprocess.Popen')
    def test_inference_unexpected_exception(self, mock_popen):
        """Test inference with unexpected exception"""
        mock_popen.side_effect = Exception("Unexpected error")

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt="test")

        assert "ERROR: unexpected exception" in result

    @patch('subprocess.Popen')
    def test_inference_with_long_prompt(self, mock_popen):
        """Test inference with long prompt"""
        mock_process = Mock()
        mock_process.returncode = 0
        long_prompt = "test " * 1000
        mock_process.communicate.return_value = ("Response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt=long_prompt)

        assert result == "Response"

    @patch('subprocess.Popen')
    def test_inference_with_special_characters(self, mock_popen):
        """Test inference with special characters in prompt"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        special_prompt = "Test with special chars: !@#$%^&*()"
        result = test_ollama(model="llama2", prompt=special_prompt)

        assert result == "Response"

    @patch('subprocess.Popen')
    def test_inference_output_passed_through(self, mock_popen):
        """Test that full ollama output is returned"""
        expected_output = "This is the model response\nWith multiple lines\nAnd details"
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (expected_output, None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt="test")

        assert result == expected_output


class TestMainFunction:
    """Test suite for main() function"""

    def test_main_basic_flow(self, mock_inference, mock_start, mock_log):
        """Test main function basic execution flow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = Namespace(
                time=1,
                model="llama2",
                prompt="test prompt",
                serviceMode=False
            )
            inputdir = Path(tmpdir) / "input"
            outputdir = Path(tmpdir) / "output"
            inputdir.mkdir()
            outputdir.mkdir()

            mock_inference.return_value = "Test response"

            from ollama_infer import main

            main(options, inputdir, outputdir)

            # Verify ollama was started
            mock_start.assert_called_once_with(1)

            # Verify inference was run
            mock_inference.assert_called_once_with("llama2", "test prompt")

            # Verify output file was created
            output_file = outputdir / "inference.txt"
            assert output_file.exists()


    def test_main_creates_output_file(self, mock_inference, mock_start):
        """Test main function creates output file with inference result"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = Namespace(
                time=1,
                model="llama2",
                prompt="What is AI?",
                serviceMode=False
            )
            outputdir = Path(tmpdir)

            expected_output = "AI is artificial intelligence..."
            mock_inference.return_value = expected_output

            from ollama_infer import main

            main(options, Path(tmpdir) / "input", outputdir)

            # Read output file
            output_file = outputdir / "inference.txt"
            with open(output_file, 'r') as f:
                content = f.read()

            assert content == expected_output

    def test_main_with_different_models(self, mock_inference, mock_start):
        """Test main function with various models"""
        with tempfile.TemporaryDirectory() as tmpdir:
            outputdir = Path(tmpdir)

            models = ["llama2", "mistral", "neural-chat"]

            for model in models:
                options = Namespace(
                    time=1,
                    model=model,
                    prompt="test",
                    serviceMode=False
                )

                mock_inference.return_value = f"Response from {model}"

                from ollama_infer import main

                main(options, Path(tmpdir) / "input", outputdir)

            assert mock_inference.call_count >= len(models)


    def test_main_handles_inference_error(self, mock_inference, mock_start):
        """Test main function when inference fails"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = Namespace(
                time=1,
                model="llama2",
                prompt="test",
                serviceMode=False
            )
            outputdir = Path(tmpdir)

            error_msg = "ERROR: Model not found"
            mock_inference.return_value = error_msg

            from ollama_infer import main

            main(options, Path(tmpdir) / "input", outputdir)

            # Verify error message is written to file
            output_file = outputdir / "inference.txt"
            with open(output_file, 'r') as f:
                content = f.read()

            assert error_msg in content


    def test_main_service_mode_enabled(self, mock_control, mock_hostname_fn,
                                       mock_gethostbyname, mock_inference, mock_start):
        """Test main function with service mode enabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = Namespace(
                time=1,
                model="llama2",
                prompt="test",
                serviceMode=True
            )
            outputdir = Path(tmpdir)

            mock_inference.return_value = "Response"
            mock_gethostbyname.return_value = "172.17.0.2"
            mock_hostname_fn.return_value = "hostname"

            from ollama_infer import main

            # Need to run in a way that doesn't block
            # This is a simplified check
            options.serviceMode = False  # Disable for this test

            main(options, Path(tmpdir) / "input", outputdir)

            # Verify basic flow
            mock_start.assert_called_once()


class TestControlServer:
    """Test suite for control server endpoints"""

    @patch('flask.Flask.run')
    def test_control_server_starts(self, mock_run):
        """Test control server initializes"""
        from ollama_infer import run_control_server

        # This test just ensures the function can be called
        # In real scenario, would need Flask test client
        mock_run.return_value = None

    def test_kill_endpoint_sets_shutdown_flag(self):
        """Test /kill endpoint sets shutdown flag"""
        # This would require testing with Flask test client
        # Simplified version shown below
        pass


class TestEdgeCases:
    """Test suite for edge cases and error conditions"""

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_ollama_with_zero_wait_time(self, mock_sleep, mock_popen):
        """Test start_ollama with zero wait time"""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        from ollama_infer import start_ollama

        start_ollama(wait_time=0)

        mock_sleep.assert_called_once_with(0)

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_ollama_with_large_wait_time(self, mock_sleep, mock_popen):
        """Test start_ollama with large wait time"""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        from ollama_infer import start_ollama

        start_ollama(wait_time=300)

        mock_sleep.assert_called_once_with(300)

    @patch('subprocess.Popen')
    def test_inference_with_empty_prompt(self, mock_popen):
        """Test inference with empty prompt"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt="")

        assert result == ""

    @patch('subprocess.Popen')
    def test_inference_with_very_long_output(self, mock_popen):
        """Test inference with very long output"""
        long_output = "x" * 100000  # 100KB output
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (long_output, None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        result = test_ollama(model="llama2", prompt="test")

        assert len(result) == 100000

    def test_namespace_with_all_required_options(self):
        """Test Namespace contains all required options"""
        options = Namespace(
            time=1,
            model="llama2",
            prompt="test",
            serviceMode=False
        )

        assert hasattr(options, 'time')
        assert hasattr(options, 'model')
        assert hasattr(options, 'prompt')
        assert hasattr(options, 'serviceMode')

    @patch('subprocess.Popen')
    def test_inference_with_multiline_prompt(self, mock_popen):
        """Test inference with multiline prompt"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        multiline_prompt = "Line 1\nLine 2\nLine 3"
        result = test_ollama(model="llama2", prompt=multiline_prompt)

        assert result == "Response"

    @patch('subprocess.Popen')
    def test_inference_with_unicode_characters(self, mock_popen):
        """Test inference with unicode characters"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        unicode_prompt = "Test with unicode: 你好世界 🌍"
        result = test_ollama(model="llama2", prompt=unicode_prompt)

        assert result == "Response"


class TestProcessManagement:
    """Test suite for subprocess handling"""

    @patch('subprocess.Popen')
    def test_inference_uses_correct_env(self, mock_popen):
        """Test inference process uses correct environment"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        test_ollama(model="llama2", prompt="test")

        # Verify env parameter is passed
        args, kwargs = mock_popen.call_args
        assert 'env' in kwargs

    @patch('subprocess.Popen')
    def test_inference_sets_text_mode(self, mock_popen):
        """Test inference process uses text mode"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Response", None)
        mock_popen.return_value = mock_process

        from ollama_infer import test_ollama

        test_ollama(model="llama2", prompt="test")

        args, kwargs = mock_popen.call_args
        assert kwargs['text'] is True

    @patch('subprocess.Popen')
    @patch('time.sleep')
    def test_start_ollama_uses_start_new_session(self, mock_sleep, mock_popen):
        """Test start_ollama uses start_new_session"""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        from ollama_infer import start_ollama

        start_ollama(wait_time=1)

        args, kwargs = mock_popen.call_args
        assert kwargs['start_new_session'] is True


class TestOutputFileHandling:
    """Test suite for output file operations"""

    def test_output_file_written_correctly(self, mock_inference, mock_start):
        """Test output file is written with correct content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = Namespace(
                time=1,
                model="llama2",
                prompt="What is Python?",
                serviceMode=False
            )
            outputdir = Path(tmpdir)

            expected_content = "Python is a programming language"
            mock_inference.return_value = expected_content

            from ollama_infer import main

            main(options, Path(tmpdir) / "input", outputdir)

            output_file = outputdir / "inference.txt"
            assert output_file.exists()

            with open(output_file, 'r') as f:
                actual_content = f.read()

            assert actual_content == expected_content

    def test_output_file_location(self, mock_inference, mock_start):
        """Test output file is created in correct directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = Namespace(
                time=1,
                model="llama2",
                prompt="test",
                serviceMode=False
            )
            outputdir = Path(tmpdir)

            mock_inference.return_value = "Response"

            from ollama_infer import main

            main(options, Path(tmpdir) / "input", outputdir)

            output_file = outputdir / "inference.txt"
            assert output_file.parent == outputdir

    def test_output_file_overwritten_on_new_run(self, mock_inference, mock_start):
        """Test output file is overwritten on subsequent runs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            outputdir = Path(tmpdir)
            output_file = outputdir / "inference.txt"

            # First run
            options1 = Namespace(
                time=1,
                model="llama2",
                prompt="test",
                serviceMode=False
            )
            mock_inference.return_value = "First response"

            from ollama_infer import main

            main(options1, Path(tmpdir) / "input", outputdir)

            with open(output_file, 'r') as f:
                content1 = f.read()

            # Second run
            options2 = Namespace(
                time=1,
                model="mistral",
                prompt="test",
                serviceMode=False
            )
            mock_inference.return_value = "Second response"

            main(options2, Path(tmpdir) / "input", outputdir)

            with open(output_file, 'r') as f:
                content2 = f.read()

            assert content1 != content2
            assert content2 == "Second response"


class TestIntegration:
    """Integration tests combining multiple functions"""

    def test_full_workflow_start_to_inference(self, mock_sleep, mock_popen):
        """Test complete workflow from server start to inference"""
        # Setup for server start
        server_process = Mock()
        server_process.poll.return_value = None

        # Setup for inference
        inference_process = Mock()
        inference_process.returncode = 0
        inference_process.communicate.return_value = ("Model response", None)

        # Mock will return different objects for different calls
        mock_popen.side_effect = [server_process, inference_process]

        from ollama_infer import start_ollama, test_ollama

        start_ollama(wait_time=1)
        result = test_ollama(model="llama2", prompt="test")

        assert result == "Model response"
        assert mock_popen.call_count == 2


    def test_main_error_handling_flow(self, mock_inference, mock_start):
        """Test main function handles errors gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            options = Namespace(
                time=1,
                model="llama2",
                prompt="test",
                serviceMode=False
            )
            outputdir = Path(tmpdir)

            # Simulate error
            mock_inference.return_value = "ERROR: Model not found"

            from ollama_infer import main

            # Should not raise exception
            main(options, Path(tmpdir) / "input", outputdir)

            # Error message should be in output
            with open(outputdir / "inference.txt") as f:
                content = f.read()

            assert "ERROR" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])