# Changelog

## 2025-01-03
### Changed
- Refactored `update_server.py` to improve readability, modularity, and maintainability.
  - Moved directory paths and content types to class-level attributes for better organization.
  - Added helper methods `is_valid_path` and `get_content_type` to encapsulate logic and avoid repetition.
  - Improved error handling for consistent and informative messages.
  - Enhanced readability with added docstrings and improved method/variable naming.
- Refactored `auth_server.py` to reduce lines of code while maintaining functionality.
  - Combined related operations to streamline logic.
  - Simplified methods for better efficiency and readability.
  - Enhanced error handling and response management.