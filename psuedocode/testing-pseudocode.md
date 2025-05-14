/tests/
├── conftest.py # Test configuration and fixtures (defined above)
├── unit/ # Unit tests (testing individual components in isolation)
│ ├── models/ # Model tests
│ ├── services/ # Service tests
│ ├── controllers/ # Controller tests
│ ├── plugins/ # Plugin tests
│ └── utils/ # Utility tests
├── integration/ # Integration tests (testing interactions between components)
│ ├── test_api_endpoints.py # API integration tests
│ ├── test_auth_flow.py # Authentication flow tests
│ ├── test_report_flow.py # Report generation flow tests
│ └── test_plugin_flow.py # Plugin integration tests
└── e2e/ # End-to-end tests (testing full user journeys via UI)
├── test_dashboard_page.py # Dashboard e2e tests
├── test_reports_page.py # Reports e2e tests
└── test_settings_page.py # Settings e2e tests
