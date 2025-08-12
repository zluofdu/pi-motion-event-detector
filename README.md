# Motion Event Detector

This project implements a motion detection system that captures human motion at night, supports scheduling, stores detected events in a local database, and sends a summary email every morning at 10 AM.

## Project Structure

```
motion-event
├── src
│   ├── main.py          # Entry point of the application
│   ├── detector.py      # Handles motion detection
│   ├── scheduler.py     # Manages scheduling of tasks
│   ├── database.py      # Interacts with the local database
│   ├── emailer.py       # Manages sending emails
│   └── config.py        # Configuration settings
├── requirements.txt     # Project dependencies
└── README.md            # Project documentation
```

## Features

- **Motion Detection**: Captures motion events during the night using a PIR sensor.
- **Event Storage**: Stores detected motion events in a local database for later retrieval.
- **Email Notifications**: Sends a summary email every morning at 10 AM with the motion events detected the previous night.
- **Scheduling**: Allows for scheduling of tasks, including email summaries.

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd motion-event
   ```

2. **Install dependencies**:
   Ensure you have Python installed, then run:
   ```
   pip install -r requirements.txt
   ```

3. **Configure the project**:
   Edit `src/config.py` to set up your database connection details and email server settings.

4. **Run the application**:
   Execute the main script to start monitoring for motion events:
   ```
   python src/main.py
   ```

## Usage

- The system will monitor for motion events at night.
- Detected events will be stored in the database.
- A summary email will be sent every morning at 10 AM containing the motion events from the previous night.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.