# Project Memory - Smart File Manager

## Tech Stack
- Python + PyQt6 desktop application
- Catppuccin theme system (Mocha dark / Latte light)
- MySQL database backend
- QSS stylesheets in ui/styles.py for global theming

## Key Decisions
- 2026-06-13: classify_tab.py uses QTableView (not QTableWidget), but QSS only targeted QTableWidget. Fixed by adding QTableView to the same selectors in styles.py so alternating row colors respect the theme (dark: #181825/#1e1e2e, light: #ffffff/#f5f5f9).
- 2026-06-13: Fixed right-click context menu "file path invalid: False" bug with three-layer defense: (1) DataLoadWorker.run() sanitizes file_path after DB fetch, (2) _populate_table sanitizes for global cache data, (3) _show_context_menu has DB fallback. Also fixed sorting proxy model row mismatch: indexAt() + mapToSource() instead of raw rowAt().
