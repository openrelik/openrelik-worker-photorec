import pytest
from unittest import mock
from pathlib import Path as ActualPath # To distinguish from mocked Path
import os
import sys

# --- Diagnostic ---
import src
print(f"DEBUG: Imported 'src' module is: {src}")
print(f"DEBUG: Path of 'src' module: {getattr(src, '__file__', 'N/A (not a file-based module)')}")
print(f"DEBUG: Contents of 'src' module: {dir(src)}")
# --- End Diagnostic ---

# Path to the module being tested, used for patching
MODULE_PATH = "src.tasks"

class MockOutputFileInstance:
    """Helper class to mock the object returned by create_output_file."""
    def __init__(self, path, display_name, **kwargs):
        self.path = path
        self.display_name = display_name
        self.kwargs = kwargs
        self._dict_representation = {"path": path, "display_name": display_name}
        self._dict_representation.update(kwargs)

    def to_dict(self):
        return self._dict_representation

@mock.patch(f"{MODULE_PATH}.logger")
@mock.patch(f"{MODULE_PATH}.uuid4")
@mock.patch(f"{MODULE_PATH}.create_task_result")
@mock.patch(f"{MODULE_PATH}.os.rename")
@mock.patch(f"{MODULE_PATH}.Path") 
@mock.patch(f"{MODULE_PATH}.os.path.isdir")
@mock.patch(f"{MODULE_PATH}.os.mkdir")
@mock.patch(f"{MODULE_PATH}.subprocess.Popen")
@mock.patch(f"{MODULE_PATH}.create_output_file")
@mock.patch(f"{MODULE_PATH}.get_input_files")
def test_command_success(
    mock_get_input_files,
    mock_create_output_file,
    mock_subprocess_popen,
    mock_os_mkdir,
    mock_os_path_isdir,
    MockPath_constructor,
    mock_os_rename,
    mock_create_task_result,
    mock_uuid4,
    mock_logger,
    tmp_path
):
    """
    Tests the photorec command task for a successful execution path.
    """
    # Import the task function here to ensure mocks are active during import resolution if needed.
    from src.tasks import command as photorec_command_task

    # --- Arrange ---
    mock_uuid_val = "testuuid123abc"
    mock_uuid4.return_value.hex = mock_uuid_val

    output_dir_str = str(tmp_path)
    workflow_id_val = "test_workflow_id_789"
    
    input_files_data = [
        {"path": "/testdata/input/image.dd", "display_name": "image.dd", "id": "input_file_id_1"}
    ]
    mock_get_input_files.return_value = input_files_data

    # Mocking create_output_file return values
    # Path for the log file (this path will be used in `with open(...)`)
    log_file_mock_path = str(tmp_path / "photorec_log.txt")
    mock_log_output = MockOutputFileInstance(
        path=log_file_mock_path,
        display_name=input_files_data[0]["display_name"],
        extension=".txt",
        data_type="text/plain"
    )

    # Path for the extracted file (this path will be used as destination in os.rename)
    extracted_file_mock_path = str(tmp_path / "recovered_file.jpg")
    mock_extracted_output = MockOutputFileInstance(
        path=extracted_file_mock_path,
        display_name="f100234.jpg", # Example name of a recovered file
        original_path="recup_dir.1/f100234.jpg",
        data_type="extraction:image_export:file",
        source_file_id=input_files_data[0]["id"]
    )
    mock_create_output_file.side_effect = [mock_log_output, mock_extracted_output]

    # Mock subprocess.Popen
    mock_popen_instance = mock.Mock()
    mock_subprocess_popen.return_value = mock_popen_instance

    # Expected directory paths
    expected_base_export_dir = os.path.join(output_dir_str, mock_uuid_val)
    expected_photorec_output_dir = expected_base_export_dir + ".1"

    # Mock os.path.isdir to simulate the existence of photorec's output directory
    mock_os_path_isdir.return_value = True

    # Mock Path object interactions for the photorec output directory
    mock_photorec_output_path_obj = mock.Mock(spec=ActualPath)
    # Configure what Path(expected_photorec_output_dir) returns
    def path_constructor_side_effect(p_arg):
        if str(p_arg) == expected_photorec_output_dir:
            return mock_photorec_output_path_obj
        return ActualPath(p_arg) # Fallback to real Path for other usages if any
    MockPath_constructor.side_effect = path_constructor_side_effect

    # Mock file found by photorec within its output directory
    mock_recovered_file_path_obj = mock.Mock(spec=ActualPath)
    mock_recovered_file_path_obj.name = "f100234.jpg"
    mock_recovered_file_path_obj.is_file.return_value = True
    # This absolute path is what photorec might produce, and is the source for os.rename
    mock_recovered_file_path_obj.absolute.return_value = ActualPath(os.path.join(expected_photorec_output_dir, "recup_dir.1", "f100234.jpg"))
    mock_recovered_file_path_obj.relative_to.return_value = ActualPath("recup_dir.1/f100234.jpg")

    mock_photorec_output_path_obj.glob.return_value = [mock_recovered_file_path_obj]

    # Mock the final result assembly
    final_task_result_mock = {"result": "success_marker"}
    mock_create_task_result.return_value = final_task_result_mock
    
    task_config_data = {"everything": True, "jpg": True} # Current code hardcodes options
    # This is the configuration for the photorec command, which is passed to the task.
    # The task is bound, so 'self' is the first argument.
    mock_celery_self = mock.Mock()
    actual_result = photorec_command_task(
        self=mock_celery_self,
        pipe_result=None,
        input_files=None, 
        output_path=output_dir_str,
        workflow_id=workflow_id_val,
        task_config=task_config_data
    )

    # --- Assert ---
    assert actual_result == final_task_result_mock

    mock_get_input_files.assert_called_once_with(None, [])
    mock_uuid4.assert_called_once()
    mock_os_mkdir.assert_called_once_with(expected_base_export_dir)

    # Assert photorec command execution
    expected_photorec_base_cmd = ["photorec", '/debug', '/log', '/d', expected_base_export_dir, '/cmd']
    expected_photorec_full_cmd = expected_photorec_base_cmd + [
        input_files_data[0]["path"],
        'fileopt,everything,enable,jpg,enable,freespace,search'
    ]
    mock_subprocess_popen.assert_called_once()
    popen_call_args = mock_subprocess_popen.call_args[0][0] 
    popen_call_kwargs = mock_subprocess_popen.call_args[1] 
    assert popen_call_args == expected_photorec_full_cmd
    assert isinstance(popen_call_kwargs["stdout"], mock.mock_IO) 

    # Assert create_output_file calls
    mock_create_output_file.assert_any_call(
        output_dir_str,
        display_name=input_files_data[0]["display_name"],
        extension=".txt",
        data_type="text/plain",
    )
    
    # Assert directory and file discovery logic
    mock_os_path_isdir.assert_called_once_with(expected_photorec_output_dir)
    MockPath_constructor.assert_any_call(expected_photorec_output_dir) 
    mock_photorec_output_path_obj.glob.assert_called_once_with("**/*")

    # 2. For the extracted file
    mock_recovered_file_path_obj.relative_to.assert_called_once_with(mock_photorec_output_path_obj)
    mock_create_output_file.assert_any_call(
        output_dir_str,
        display_name=mock_recovered_file_path_obj.name,
        original_path=str(mock_recovered_file_path_obj.relative_to.return_value),
        data_type="extraction:image_export:file",
        source_file_id=input_files_data[0]["id"],
    )
    assert mock_create_output_file.call_count == 2 

    # Assert file rename operation
    mock_recovered_file_path_obj.absolute.assert_called_once()
    mock_os_rename.assert_called_once_with(
        mock_recovered_file_path_obj.absolute.return_value,
        mock_extracted_output.path  
    )

    # Assert final result creation
    expected_output_files_for_result = [
        mock_log_output.to_dict(),
        mock_extracted_output.to_dict()
    ]
    mock_create_task_result.assert_called_once_with(
        output_files=expected_output_files_for_result,
        workflow_id=workflow_id_val,
        command=expected_photorec_base_cmd,
        meta={},
    )

    mock_logger.info.assert_any_call('command' + str(expected_photorec_full_cmd))
    mock_logger.info.assert_any_call('export_directory_out is: ' + str(mock_photorec_output_path_obj))
    mock_logger.info.assert_any_call('directory found')
    mock_logger.info.assert_any_call(f"'{mock_recovered_file_path_obj.name}' is a file.")