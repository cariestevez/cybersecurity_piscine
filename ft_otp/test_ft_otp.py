import unittest
from unittest.mock import mock_open, patch
import os
from ft_otp import validate_hex_key  # Import the function to test
from ft_otp import save_key_securely
from ft_otp import process_g_option
import tempfile

class TestFtOtp(unittest.TestCase):
    def test_valid_key(self):
        valid_key = "a" * 64
        try:
            validate_hex_key(valid_key)
        except ValueError:
            self.fail("validate_hex_key raised ValueError unexpectedly!")

    def test_short_key(self):
        short_key = "a" * 63
        with self.assertRaises(ValueError):
            validate_hex_key(short_key)

    def test_invalid_characters(self):
        invalid_key = "z" * 64 
        with self.assertRaises(ValueError):
            validate_hex_key(invalid_key)
    
    def test_empty_key(self):
        empty_key = ""
        with self.assertRaises(ValueError):
            validate_hex_key(empty_key)

    @patch("builtins.open", new_callable=mock_open)  # Mock the open function
    @patch("os.chmod")  # Mock the os.chmod function
    def test_save_key_securely(self, mock_chmod, mock_file):
        key_data = "test_key_data"
        filename = "ft_otp.key"

        save_key_securely(key_data, filename)

        # Check if the file was opened in write mode
        mock_file.assert_called_once_with(filename, "w")
        
       # Extract the written key from the mock
        written_key = mock_file().write.call_args.args[0]

        # Assert that the file was written with the correct (processed) key
        self.assertEqual(written_key, "f14880ac3b2546c8b5fff768a0444dd30a40f8bf6679e366cb0867b3ede56519")
            
        # Check if the correct file permissions were set
        mock_chmod.assert_called_once_with(filename, 0o400)  # 0o400 = read-only for owner
    
    @patch("ft_otp.save_key_securely")  # Mock the save_key_securely function
    def test_valid_key(self, mock_save):
        valid_key = "a" * 64
        process_g_option(valid_key)
        
        # Ensure save_key_securely was called with the correct parameters
        mock_save.assert_called_once_with(valid_key)

    def test_invalid_key_short(self):
        short_key = "a" * 63
        with self.assertRaises(ValueError):
            process_g_option(short_key)

    def test_invalid_key_characters(self):
        invalid_key = "z" * 64
        with self.assertRaises(ValueError):
            process_g_option(invalid_key)

if __name__ == "__main__":
    unittest.main()
