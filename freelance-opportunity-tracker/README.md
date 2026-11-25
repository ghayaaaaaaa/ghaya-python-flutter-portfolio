# Freelance Opportunity Tracker

An offline-first Flutter app for organizing a shortlist of freelance opportunities. Add a role, record its source link and budget, search notes, and move it through a small set of personal statuses.

This AI-assisted portfolio demonstration was prepared for Ghaya. It stores records in the device's standard app preferences through `shared_preferences`. It does not connect to a marketplace, scrape listings, send proposals, or sync data to a server. The app does not encrypt these records; do not save highly sensitive personal, client, or account information.

## Features

- Adaptive dashboard with live totals for all opportunities, saved leads, applications, and interviews.
- Status filters display counts so the shortlist is easy to scan at a glance.
- Responsive layout that keeps the summary and add flow usable on mobile and wide screens.
- Create, edit, and delete opportunity records.
- Search titles, platforms, budgets, links, and notes.
- Filter by saved, applied, interviewing, and archived status.
- Persist records locally as JSON.
- Handle loading, empty, validation, and storage-error states.
- Use a responsive one- or two-column layout.

## Requirements

- Flutter 3.16.9 or newer.
- Dart 3.2.6 or newer.
- Android SDK to build an Android package.

The dependency is pinned to shared_preferences 2.2.3 to support the project SDK baseline. No API keys or backend account are required.

## Run

From this directory:

    flutter pub get
    flutter run

Records stay in the device's local preferences store. Uninstalling the app or clearing app data may remove them. The Android application ID and release signing are demo placeholders; this project does not claim store publication or a production release.

## Architecture

The UI lives under lib/features, the opportunity model under lib/domain, and local persistence behind a repository under lib/data. The view model owns loading, filtering, and mutations. This keeps storage and interface concerns separate without adding a large state-management dependency.

## Portfolio attribution

Prepared with AI assistance for Ghaya's portfolio. The app contains no real job listings or client data.

## License

No open-source license is included with this portfolio sample.


