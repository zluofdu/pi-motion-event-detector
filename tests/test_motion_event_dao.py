import unittest
import os
import datetime
from src.motion_event_dao import MotionEventDao
from src.models.motion_event import MotionEvent, Base
from sqlalchemy import create_engine

class TestMotionEventDao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a test database file
        cls.test_db_path = 'test_motion_events.db'
        cls.db_url = f'sqlite:///{cls.test_db_path}'
        cls.dao = MotionEventDao(db_url=cls.db_url)

    @classmethod
    def tearDownClass(cls):
        # Clean up the test database file
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def setUp(self):
        # Start each test with an empty database
        engine = create_engine(self.db_url)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    def test_add_event(self):
        # Arrange
        start_time = datetime.datetime(2025, 8, 11, 20, 0, 0)  # 8:00 PM
        stop_time = datetime.datetime(2025, 8, 11, 20, 0, 10)  # 10 seconds later
        event = MotionEvent(
            device_id="test_device_1",
            start_timestamp=start_time,
            stop_timestamp=stop_time
        )

        # Act
        self.dao.add(event)

        # Assert
        saved_event = self.dao.get(1)  # First event should have id=1
        self.assertIsNotNone(saved_event)
        self.assertEqual(saved_event.device_id, "test_device_1")
        self.assertEqual(saved_event.start_timestamp, start_time)
        self.assertEqual(saved_event.stop_timestamp, stop_time)

    def test_get_nonexistent_event(self):
        # Act
        event = self.dao.get(999)

        # Assert
        self.assertIsNone(event)

    def test_list_events_with_time_filter(self):
        # Arrange
        # Create events at different times
        events = [
            MotionEvent(
                device_id="test_device_1",
                start_timestamp=datetime.datetime(2025, 8, 11, 19, 0),  # 7:00 PM
                stop_timestamp=datetime.datetime(2025, 8, 11, 19, 1)
            ),
            MotionEvent(
                device_id="test_device_1",
                start_timestamp=datetime.datetime(2025, 8, 11, 20, 0),  # 8:00 PM
                stop_timestamp=datetime.datetime(2025, 8, 11, 20, 1)
            ),
            MotionEvent(
                device_id="test_device_1",
                start_timestamp=datetime.datetime(2025, 8, 11, 21, 0),  # 9:00 PM
                stop_timestamp=datetime.datetime(2025, 8, 11, 21, 1)
            )
        ]
        for event in events:
            self.dao.add(event)

        # Act
        # Get events between 7:30 PM and 8:30 PM
        start_filter = datetime.datetime(2025, 8, 11, 19, 30)
        end_filter = datetime.datetime(2025, 8, 11, 20, 30)
        filtered_events = self.dao.list(start_filter, end_filter)

        # Assert
        self.assertEqual(len(filtered_events), 1)
        # Check for the event in the expected time window
        event = filtered_events[0]
        self.assertEqual(event.device_id, "test_device_1")
        self.assertEqual(event.start_timestamp.hour, 20)  # 8:00 PM

    def test_list_all_events(self):
        # Arrange
        events = [
            MotionEvent(device_id="test_device_1",
                       start_timestamp=datetime.datetime.now(),
                       stop_timestamp=datetime.datetime.now()),
            MotionEvent(device_id="test_device_1",
                       start_timestamp=datetime.datetime.now(),
                       stop_timestamp=datetime.datetime.now())
        ]
        for event in events:
            self.dao.add(event)

        # Act
        all_events = self.dao.list()

        # Assert
        self.assertEqual(len(all_events), 2)
        # Verify all events have the correct device ID
        for event in all_events:
            self.assertEqual(event.device_id, "test_device_1")

if __name__ == '__main__':
    unittest.main()
