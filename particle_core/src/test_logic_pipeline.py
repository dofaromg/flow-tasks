import unittest
import os
import json
from datetime import datetime, timezone
from logic_pipeline import LogicPipeline

class TestLogicPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = LogicPipeline()
        self.test_output_dir = "test_output"
        os.makedirs(self.test_output_dir, exist_ok=True)

    def tearDown(self):
        for f in os.listdir(self.test_output_dir):
            os.remove(os.path.join(self.test_output_dir, f))
        os.rmdir(self.test_output_dir)

    def test_store_result_timestamp_consistency(self):
        """Tests if the timestamp in the filename and content are consistent."""
        input_val = "test_input"
        result = "test_result"

        # Mock datetime.now() to simulate a different timezone
        from unittest.mock import patch
        mock_now = datetime(2025, 1, 1, 12, 0, 0)

        from unittest.mock import patch, MagicMock
        # Simulate that datetime.now() is 8 hours ahead of utcnow()
        mock_now = datetime(2025, 1, 1, 20, 0, 0)
        mock_utcnow = datetime(2025, 1, 1, 12, 0, 0)

        with patch('logic_pipeline.datetime', wraps=datetime) as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.utcnow.return_value = mock_utcnow

            # Store the result
            filename = self.pipeline.store_result(input_val, result, output_dir=self.test_output_dir)

            # Extract timestamp from filename
            file_timestamp_str = os.path.basename(filename).replace("logic_result_", "").replace(".json", "")
            file_timestamp = datetime.strptime(file_timestamp_str, "%Y%m%d_%H%M%S")

            # Read timestamp from file content
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                content_timestamp_str = data["timestamp"]
                content_timestamp = datetime.fromisoformat(content_timestamp_str).replace(tzinfo=None)

            # Check if timestamps are close (within a reasonable delta, e.g., 2 seconds)
            time_difference = abs((file_timestamp - content_timestamp).total_seconds())
            self.assertLess(time_difference, 2, "Timestamp in filename and content should be consistent (UTC)")

if __name__ == '__main__':
    unittest.main()
