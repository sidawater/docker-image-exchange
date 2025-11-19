"""
Unit tests for core.manager.knowledge module
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from core.manager.knowledge import Knowledge


class TestKnowledge:
    """Test Knowledge class"""

    def setup_method(self):
        """Create a temporary directory structure for testing"""
        self.test_dir = tempfile.mkdtemp()

        # Create test directory structure
        self.knowledge_dir = os.path.join(self.test_dir, "knowledge_base")
        os.makedirs(self.knowledge_dir)

        # Create some test files
        self.create_test_structure()

    def create_test_structure(self):
        """Create test directory structure"""
        # Root files
        Path(self.knowledge_dir, "README.md").write_text("# Knowledge Base")
        Path(self.knowledge_dir, "index.md").write_text("Index file")

        # Subdirectories with files
        dir1 = os.path.join(self.knowledge_dir, "section1")
        os.makedirs(dir1)
        Path(dir1, "file1.md").write_text("Content 1")
        Path(dir1, "file2.md").write_text("Content 2")

        # Nested subdirectory
        dir2 = os.path.join(dir1, "subsection")
        os.makedirs(dir2)
        Path(dir2, "nested_file.md").write_text("Nested content")

        # Another top-level section
        dir3 = os.path.join(self.knowledge_dir, "section2")
        os.makedirs(dir3)
        Path(dir3, "another_file.md").write_text("More content")

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_knowledge_initialization_with_valid_path(self):
        """Test initializing Knowledge with a valid directory path"""
        knowledge = Knowledge(self.knowledge_dir)

        assert knowledge.base_path == Path(self.knowledge_dir).resolve()
        assert knowledge.count_files() == 6  # README, index, file1, file2, nested_file, another_file

    def test_knowledge_initialization_with_nonexistent_path(self):
        """Test initializing Knowledge with a nonexistent path raises FileNotFoundError"""
        nonexistent_path = "/path/that/does/not/exist"

        with pytest.raises(FileNotFoundError, match="Knowledge base path does not exist"):
            Knowledge(nonexistent_path)

    def test_knowledge_initialization_with_file_instead_of_directory(self):
        """Test initializing Knowledge with a file instead of directory raises NotADirectoryError"""
        # Create a temporary file
        temp_file = os.path.join(self.test_dir, "test_file.txt")
        Path(temp_file).write_text("test")

        with pytest.raises(NotADirectoryError, match="Path is not a directory"):
            Knowledge(temp_file)

    def test_list_files(self):
        """Test list_files method returns all files"""
        knowledge = Knowledge(self.knowledge_dir)

        files = knowledge.list_files()

        assert len(files) == 6
        file_names = [f['name'] for f in files]
        assert "README.md" in file_names
        assert "index.md" in file_names
        assert "file1.md" in file_names
        assert "file2.md" in file_names
        assert "nested_file.md" in file_names
        assert "another_file.md" in file_names

    def test_count_files(self):
        """Test count_files method"""
        knowledge = Knowledge(self.knowledge_dir)

        assert knowledge.count_files() == 6

        # Add another file
        Path(self.knowledge_dir, "new_file.md").write_text("New content")

        # Need to re-initialize to scan again, or call _scan()
        knowledge._scan()
        assert knowledge.count_files() == 7

    def test_get_structure(self):
        """Test get_structure method returns correct hierarchical structure"""
        knowledge = Knowledge(self.knowledge_dir)

        structure = knowledge.get_structure()

        # Check root structure
        assert structure['root'] == Path(self.knowledge_dir).name
        assert structure['path'] == str(Path(self.knowledge_dir).resolve())
        assert 'files' in structure
        assert 'directories' in structure

        # Check that root files are present
        root_files = structure['files']
        assert len(root_files) == 2
        root_file_names = [f['name'] for f in root_files]
        assert "README.md" in root_file_names
        assert "index.md" in root_file_names

        # Check that section1 directory exists
        assert 'section1' in structure['directories']
        section1 = structure['directories']['section1']

        # Check section1 files
        section1_files = section1['files']
        assert len(section1_files) == 2
        section1_file_names = [f['name'] for f in section1_files]
        assert "file1.md" in section1_file_names
        assert "file2.md" in section1_file_names

        # Check subsection nested directory
        assert 'subsection' in section1['directories']
        subsection = section1['directories']['subsection']
        subsection_files = subsection['files']
        assert len(subsection_files) == 1
        assert subsection_files[0]['name'] == "nested_file.md"

        # Check section2 directory
        assert 'section2' in structure['directories']
        section2 = structure['directories']['section2']
        section2_files = section2['files']
        assert len(section2_files) == 1
        assert section2_files[0]['name'] == "another_file.md"

    def test_get_file_list_with_prefix(self):
        """Test get_file_list_with_prefix method"""
        knowledge = Knowledge(self.knowledge_dir)

        # Without prefix
        file_list = knowledge.get_file_list_with_prefix()
        assert len(file_list) == 2  # Only root files

        # With prefix
        file_list = knowledge.get_file_list_with_prefix("section1")
        assert len(file_list) == 1  # The first file in section1

    @pytest.mark.asyncio
    async def test_upload_all(self):
        """Test upload_all method"""
        knowledge = Knowledge(self.knowledge_dir)

        # Mock the DocFile client
        mock_client = AsyncMock()
        mock_client.fput_object = AsyncMock()

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            # Call upload_all
            await knowledge.upload_all()

            # Verify that fput_object was called for each file
            assert mock_client.fput_object.call_count == 6

    @pytest.mark.asyncio
    async def test_upload_all_with_prefix(self):
        """Test upload_all method with prefix"""
        knowledge = Knowledge(self.knowledge_dir)

        mock_client = AsyncMock()
        mock_client.fput_object = AsyncMock()

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.upload_all(prefix="test-prefix")

            # Verify that all object names include the prefix
            for call in mock_client.fput_object.call_args_list:
                object_name = call[1]['object_name']
                assert object_name.startswith("test-prefix/")

    @pytest.mark.asyncio
    async def test_upload_all_client_not_initialized(self):
        """Test upload_all raises RuntimeError when client not initialized"""
        knowledge = Knowledge(self.knowledge_dir)

        with patch('core.manager.knowledge.DocFile.client', side_effect=RuntimeError("Client not initialized")):
            with pytest.raises(RuntimeError, match="Client not initialized"):
                await knowledge.upload_all()

    @pytest.mark.asyncio
    async def test_download_all(self):
        """Test download_all method"""
        knowledge = Knowledge(self.knowledge_dir)

        # Mock the client
        mock_client = AsyncMock()
        mock_objects = [
            Mock(object_name="README.md"),
            Mock(object_name="index.md"),
            Mock(object_name="section1/file1.md"),
            Mock(object_name="section1/file2.md"),
            Mock(object_name="section1/subsection/nested_file.md"),
            Mock(object_name="section2/another_file.md")
        ]
        mock_client.list_objects = AsyncMock(return_value=mock_objects)
        mock_client.fget_object = AsyncMock()

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.download_all()

            # Verify that fget_object was called for each object
            assert mock_client.fget_object.call_count == 6

    @pytest.mark.asyncio
    async def test_download_all_with_destination(self):
        """Test download_all method with custom destination"""
        knowledge = Knowledge(self.knowledge_dir)

        mock_client = AsyncMock()
        mock_objects = [Mock(object_name="README.md")]
        mock_client.list_objects = AsyncMock(return_value=mock_objects)
        mock_client.fget_object = AsyncMock()

        destination = os.path.join(self.test_dir, "downloads")

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.download_all(destination=destination)

            # Verify destination directory was created and used
            assert os.path.exists(destination)

    @pytest.mark.asyncio
    async def test_download_all_client_not_initialized(self):
        """Test download_all raises RuntimeError when client not initialized"""
        knowledge = Knowledge(self.knowledge_dir)

        with patch('core.manager.knowledge.DocFile.client', side_effect=RuntimeError("Client not initialized")):
            with pytest.raises(RuntimeError, match="Client not initialized"):
                await knowledge.download_all()

    @pytest.mark.asyncio
    async def test_upload_file(self):
        """Test upload_file method"""
        knowledge = Knowledge(self.knowledge_dir)

        mock_client = AsyncMock()
        mock_client.fput_object = AsyncMock()

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.upload_file("section1/file1.md")

            # Verify fput_object was called
            mock_client.fput_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_with_absolute_path(self):
        """Test upload_file method with absolute path"""
        knowledge = Knowledge(self.knowledge_dir)

        mock_client = AsyncMock()
        mock_client.fput_object = AsyncMock()

        abs_path = os.path.join(self.knowledge_dir, "section1", "file1.md")

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.upload_file(abs_path)

            mock_client.fput_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_with_nonexistent_file(self):
        """Test upload_file raises FileNotFoundError for nonexistent file"""
        knowledge = Knowledge(self.knowledge_dir)

        with pytest.raises(FileNotFoundError, match="File not found"):
            await knowledge.upload_file("nonexistent_file.md")

    @pytest.mark.asyncio
    async def test_upload_file_with_prefix(self):
        """Test upload_file with prefix"""
        knowledge = Knowledge(self.knowledge_dir)

        mock_client = AsyncMock()
        mock_client.fput_object = AsyncMock()

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.upload_file("section1/file1.md", prefix="my-prefix")

            # Verify the object name includes prefix
            call_args = mock_client.fput_object.call_args
            object_name = call_args[1]['object_name']
            assert object_name.startswith("my-prefix/")

    @pytest.mark.asyncio
    async def test_upload_file_client_not_initialized(self):
        """Test upload_file raises RuntimeError when client not initialized"""
        knowledge = Knowledge(self.knowledge_dir)

        with patch('core.manager.knowledge.DocFile.client', side_effect=RuntimeError("Client not initialized")):
            with pytest.raises(RuntimeError, match="Client not initialized"):
                await knowledge.upload_file("README.md")

    @pytest.mark.asyncio
    async def test_download_file(self):
        """Test download_file method"""
        knowledge = Knowledge(self.knowledge_dir)

        mock_client = AsyncMock()
        mock_client.fget_object = AsyncMock()

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.download_file("test-object.txt")

            mock_client.fget_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file_with_destination(self):
        """Test download_file with custom destination"""
        knowledge = Knowledge(self.knowledge_dir)

        mock_client = AsyncMock()
        mock_client.fget_object = AsyncMock()

        dest = os.path.join(self.test_dir, "custom_dest.txt")

        with patch('core.manager.knowledge.DocFile.client', return_value=mock_client):
            await knowledge.download_file("test-object.txt", destination=dest)

            mock_client.fget_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file_client_not_initialized(self):
        """Test download_file raises RuntimeError when client not initialized"""
        knowledge = Knowledge(self.knowledge_dir)

        with patch('core.manager.knowledge.DocFile.client', side_effect=RuntimeError("Client not initialized")):
            with pytest.raises(RuntimeError, match="Client not initialized"):
                await knowledge.download_file("test-object.txt")

    def test_repr(self):
        """Test __repr__ method"""
        knowledge = Knowledge(self.knowledge_dir)

        repr_str = repr(knowledge)

        assert "Knowledge" in repr_str
        assert self.knowledge_dir in repr_str
        assert "files=6" in repr_str
