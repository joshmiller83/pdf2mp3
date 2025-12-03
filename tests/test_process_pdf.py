import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call
import sys
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process_pdf import (
    run_split_pdf,
    page_num,
    group_text_files,
    run_generate_audio
)


class TestPageNum:
    """Test suite for page_num function"""

    def test_extracts_single_digit_page_number(self):
        """Test extracting single digit page numbers"""
        path = Path("page_1.txt")
        assert page_num(path) == 1

    def test_extracts_multi_digit_page_number(self):
        """Test extracting multi-digit page numbers"""
        path = Path("page_123.txt")
        assert page_num(path) == 123

    def test_extracts_page_number_with_path(self):
        """Test extracting page number from full path"""
        path = Path("/some/directory/page_42.txt")
        assert page_num(path) == 42

    def test_returns_negative_one_for_no_number(self):
        """Test returns -1 when no number found"""
        path = Path("document.txt")
        assert page_num(path) == -1

    def test_extracts_last_number_before_extension(self):
        """Test extracts the number immediately before .txt"""
        path = Path("page_10_copy_5.txt")
        assert page_num(path) == 5

    def test_zero_page_number(self):
        """Test handling of zero as page number"""
        path = Path("page_0.txt")
        assert page_num(path) == 0

    def test_with_underscores(self):
        """Test page number with various underscore patterns"""
        assert page_num(Path("page_007.txt")) == 7
        assert page_num(Path("document_page_99.txt")) == 99


class TestGroupTextFiles:
    """Test suite for group_text_files function"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_groups_files_by_size(self, temp_dir):
        """Test that files are grouped according to group_size"""
        # Create 10 test files
        for i in range(1, 11):
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=3, skip=0)

        assert len(groups) == 4  # 10 files / 3 per group = 4 groups
        assert len(groups[0]) == 3
        assert len(groups[1]) == 3
        assert len(groups[2]) == 3
        assert len(groups[3]) == 1  # remainder

    def test_skip_first_n_files(self, temp_dir):
        """Test that skip parameter skips first N files"""
        # Create 10 test files
        for i in range(1, 11):
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=3, skip=5)

        # Should skip first 5, leaving 5 files
        assert len(groups) == 2  # 5 files / 3 per group = 2 groups
        # First group should start at page 6
        assert "page_6.txt" in groups[0][0].name

    def test_numeric_sorting(self, temp_dir):
        """Test that files are sorted numerically, not lexicographically"""
        # Create files in non-sequential order
        for i in [1, 2, 10, 20, 3]:
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=2, skip=0)

        # Should be sorted as: 1, 2, 3, 10, 20
        assert "page_1.txt" in groups[0][0].name
        assert "page_2.txt" in groups[0][1].name
        assert "page_3.txt" in groups[1][0].name
        assert "page_10.txt" in groups[1][1].name
        assert "page_20.txt" in groups[2][0].name

    def test_padding_width_from_highest_page(self, temp_dir):
        """Test that padding width is calculated from highest page number"""
        (temp_dir / "page_1.txt").touch()
        (temp_dir / "page_999.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=10, skip=0)

        assert pad == 3  # 999 has 3 digits

    def test_empty_directory(self, temp_dir):
        """Test handling of directory with no txt files"""
        groups, pad = group_text_files(temp_dir, group_size=3, skip=0)

        assert groups == []
        assert pad == 0

    def test_skip_all_files(self, temp_dir):
        """Test skipping more files than exist"""
        for i in range(1, 6):
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=3, skip=10)

        assert len(groups) == 0

    def test_group_size_larger_than_file_count(self, temp_dir):
        """Test group size larger than total files"""
        for i in range(1, 4):
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=10, skip=0)

        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_single_file(self, temp_dir):
        """Test with only one file"""
        (temp_dir / "page_1.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=3, skip=0)

        assert len(groups) == 1
        assert len(groups[0]) == 1

    def test_padding_with_single_digit(self, temp_dir):
        """Test padding calculation with single digit pages"""
        for i in range(1, 6):
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=2, skip=0)

        assert pad == 1  # highest is 5, single digit

    def test_ignores_non_txt_files(self, temp_dir):
        """Test that non-.txt files are ignored"""
        (temp_dir / "page_1.txt").touch()
        (temp_dir / "page_2.pdf").touch()
        (temp_dir / "page_3.txt").touch()
        (temp_dir / "readme.md").touch()

        groups, pad = group_text_files(temp_dir, group_size=10, skip=0)

        # Should only find 2 .txt files
        total_files = sum(len(g) for g in groups)
        assert total_files == 2


class TestRunSplitPdf:
    """Test suite for run_split_pdf function"""

    @patch('subprocess.run')
    def test_calls_split_pdf_script(self, mock_run):
        """Test that split_pdf.py is called with correct arguments"""
        pdf_path = Path("/path/to/test.pdf")
        output_dir = Path("/output/dir")

        run_split_pdf(pdf_path, output_dir)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]

        assert "split_pdf.py" in call_args
        assert str(pdf_path) in call_args
        assert str(output_dir) in call_args
        assert call_args[0] == sys.executable  # Uses current Python interpreter

    @patch('subprocess.run')
    def test_check_true_for_errors(self, mock_run):
        """Test that check=True is passed to raise on errors"""
        run_split_pdf(Path("test.pdf"), Path("output"))

        assert mock_run.call_args[1]['check'] is True

    @patch('subprocess.run')
    def test_with_spaces_in_path(self, mock_run):
        """Test handling of paths with spaces"""
        pdf_path = Path("/path with spaces/test.pdf")
        output_dir = Path("/output path/dir")

        run_split_pdf(pdf_path, output_dir)

        call_args = mock_run.call_args[0][0]
        assert str(pdf_path) in call_args
        assert str(output_dir) in call_args


class TestRunGenerateAudio:
    """Test suite for run_generate_audio function"""

    @patch('subprocess.run')
    def test_calls_generate_audio_script(self, mock_run):
        """Test that generate_audio.py is called with correct arguments"""
        txt_group = [Path("page_1.txt"), Path("page_2.txt")]
        output_path = Path("output.mp3")
        speed = 1.5

        run_generate_audio(txt_group, output_path, speed)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]

        assert "generate_audio.py" in call_args
        assert "page_1.txt" in call_args
        assert "page_2.txt" in call_args
        assert "--output" in call_args
        assert str(output_path) in call_args
        assert "--speed" in call_args
        assert "1.5" in call_args

    @patch('subprocess.run')
    def test_check_true_for_errors(self, mock_run):
        """Test that check=True is passed to raise on errors"""
        txt_group = [Path("page_1.txt")]
        output_path = Path("output.mp3")

        run_generate_audio(txt_group, output_path, 1.0)

        assert mock_run.call_args[1]['check'] is True

    @patch('subprocess.run')
    def test_multiple_text_files(self, mock_run):
        """Test with multiple text files"""
        txt_group = [Path(f"page_{i}.txt") for i in range(1, 6)]
        output_path = Path("pages_1-5.mp3")

        run_generate_audio(txt_group, output_path, 1.0)

        call_args = mock_run.call_args[0][0]
        for i in range(1, 6):
            assert f"page_{i}.txt" in call_args

    @patch('subprocess.run')
    def test_speed_parameter_formatting(self, mock_run):
        """Test that speed parameter is correctly formatted"""
        txt_group = [Path("page_1.txt")]
        output_path = Path("output.mp3")

        run_generate_audio(txt_group, output_path, 0.75)

        call_args = mock_run.call_args[0][0]
        speed_index = call_args.index("--speed")
        assert call_args[speed_index + 1] == "0.75"


class TestIntegration:
    """Integration tests for the process_pdf workflow"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            text_dir = temp_path / "text"
            output_dir = temp_path / "output"
            text_dir.mkdir()
            output_dir.mkdir()
            yield text_dir, output_dir

    def test_grouping_and_naming_workflow(self, temp_dirs):
        """Test the complete workflow of grouping and naming"""
        text_dir, output_dir = temp_dirs

        # Create 15 text files
        for i in range(1, 16):
            (text_dir / f"page_{i}.txt").write_text(f"Content of page {i}")

        # Group files (skip first 3, group by 4)
        groups, pad = group_text_files(text_dir, group_size=4, skip=3)

        # Should have files 4-15 (12 files) grouped into 3 groups
        assert len(groups) == 3
        assert len(groups[0]) == 4  # pages 4-7
        assert len(groups[1]) == 4  # pages 8-11
        assert len(groups[2]) == 4  # pages 12-15

        # Test output naming
        for g in groups:
            first = str(page_num(g[0])).zfill(pad)
            last = str(page_num(g[-1])).zfill(pad)
            output_file = output_dir / f"pages_{first}-{last}.mp3"

            # Verify names are formatted correctly
            assert first.isdigit()
            assert last.isdigit()
            assert int(last) > int(first)

    def test_padding_consistency(self, temp_dirs):
        """Test that padding is consistent across all output names"""
        text_dir, output_dir = temp_dirs

        # Create files with varying digit counts
        for i in [1, 2, 50, 100]:
            (text_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(text_dir, group_size=2, skip=0)

        # With max page 100, padding should be 3
        assert pad == 3

        # All output names should use 3-digit padding
        for g in groups:
            first = str(page_num(g[0])).zfill(pad)
            last = str(page_num(g[-1])).zfill(pad)

            assert len(first) == 3
            assert len(last) == 3

    @patch('subprocess.run')
    def test_error_handling_in_split_pdf(self, mock_run):
        """Test that errors from split_pdf are propagated"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')

        with pytest.raises(subprocess.CalledProcessError):
            run_split_pdf(Path("test.pdf"), Path("output"))

    @patch('subprocess.run')
    def test_error_handling_in_generate_audio(self, mock_run):
        """Test that errors from generate_audio are propagated"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')

        with pytest.raises(subprocess.CalledProcessError):
            run_generate_audio([Path("page_1.txt")], Path("output.mp3"), 1.0)

    def test_realistic_workflow(self, temp_dirs):
        """Test a realistic workflow with typical parameters"""
        text_dir, output_dir = temp_dirs

        # Simulate a 50-page document
        for i in range(1, 51):
            (text_dir / f"page_{i}.txt").write_text(f"Page {i} content.")

        # Skip TOC (first 5 pages), group by 8
        groups, pad = group_text_files(text_dir, group_size=8, skip=5)

        # Should have 45 pages grouped into 6 groups (5 full + 1 partial)
        assert len(groups) == 6
        assert sum(len(g) for g in groups) == 45

        # Verify first group starts at page 6
        assert page_num(groups[0][0]) == 6

        # Verify last group has remaining pages
        assert len(groups[-1]) == 5  # 45 % 8 = 5 remainder

        # Check padding is consistent (50 -> 2 digits)
        assert pad == 2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_group_size_of_one(self, temp_dir):
        """Test with group_size=1"""
        for i in range(1, 4):
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=1, skip=0)

        assert len(groups) == 3
        for group in groups:
            assert len(group) == 1

    def test_skip_zero(self, temp_dir):
        """Test with skip=0 (no skipping)"""
        for i in range(1, 6):
            (temp_dir / f"page_{i}.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=2, skip=0)

        # First group should start at page 1
        assert page_num(groups[0][0]) == 1

    def test_files_with_unusual_names(self, temp_dir):
        """Test with files that don't match page_N.txt pattern"""
        (temp_dir / "document.txt").touch()
        (temp_dir / "notes.txt").touch()
        (temp_dir / "page_1.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=5, skip=0)

        # Should still process all .txt files
        total_files = sum(len(g) for g in groups)
        assert total_files == 3

    def test_large_page_numbers(self, temp_dir):
        """Test with very large page numbers"""
        (temp_dir / "page_1000.txt").touch()
        (temp_dir / "page_9999.txt").touch()

        groups, pad = group_text_files(temp_dir, group_size=10, skip=0)

        assert pad == 4  # 9999 has 4 digits
