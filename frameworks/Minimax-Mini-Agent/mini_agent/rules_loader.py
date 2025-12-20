"""Rules and protocols loader with hotloading support."""

import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RulesLoader:
    """Loads and manages rules/protocols with hotloading support."""

    def __init__(self, rules_file: Optional[str] = None):
        """Initialize rules loader.

        Args:
            rules_file: Path to rules file. If None, uses portable location:
                       1) mini_agent/config/TeamADAPT_Rules.md (portable)
                       2) /home/x/Documents/master-mas/TeamADAPT_Rules.md (legacy fallback)
        """
        if rules_file is None:
            # Try portable location first
            portable_path = Path(__file__).parent / "config" / "TeamADAPT_Rules.md"
            if portable_path.exists():
                rules_file = str(portable_path)
            else:
                # Fallback to legacy location
                rules_file = "/home/x/Documents/master-mas/TeamADAPT_Rules.md"

        self.rules_file = Path(rules_file)
        self._last_loaded: Optional[float] = None
        self._last_hash: Optional[str] = None
        self._cached_rules: Optional[str] = None
        self._cache_duration = 5.0  # Cache for 5 seconds before checking for changes

    def _calculate_file_hash(self) -> str:
        """Calculate MD5 hash of rules file.

        Returns:
            MD5 hash as hex string, or empty string if file doesn't exist
        """
        if not self.rules_file.exists():
            return ""

        try:
            with open(self.rules_file, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _should_reload(self) -> bool:
        """Check if file has changed and should be reloaded.

        Returns:
            True if file should be reloaded, False otherwise
        """
        if not self.rules_file.exists():
            return False

        now = time.time()

        # Check cache expiration
        if self._last_loaded and (now - self._last_loaded) < self._cache_duration:
            return False

        # Calculate current hash
        current_hash = self._calculate_file_hash()

        # If hash changed or not loaded yet, reload
        if not self._last_hash or current_hash != self._last_hash:
            self._last_hash = current_hash
            self._last_loaded = now
            return True

        return False

    def load_rules(self, force_reload: bool = False) -> Optional[str]:
        """Load and format rules from file.

        Args:
            force_reload: Force reload even if cached

        Returns:
            Formatted rules string ready for system prompt, or None if no rules file
        """
        if not self.rules_file.exists():
            return None

        # Check if we need to reload
        should_reload = force_reload or self._should_reload()

        if not should_reload and self._cached_rules is not None:
            return self._cached_rules

        try:
            with open(self.rules_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Format rules for system prompt
            formatted = self._format_rules(content)
            self._cached_rules = formatted

            # Add hotload indicator if file changed
            if not force_reload and self._last_loaded:
                print(f"🔄 Hotloaded rules from: {self.rules_file}")

            return formatted

        except Exception as e:
            print(f"⚠️  Error loading rules from {self.rules_file}: {e}")
            return self._cached_rules

    def _format_rules(self, content: str) -> str:
        """Format rules content for system prompt.

        Args:
            content: Raw markdown content from rules file

        Returns:
            Formatted rules string for system prompt
        """
        lines = content.splitlines()
        formatted_lines = []

        formatted_lines.append("# TeamADAPT Rules & Protocols")
        formatted_lines.append("")
        formatted_lines.append("The following rules, protocols, and best practices MUST be followed:")
        formatted_lines.append("")

        for line in lines:
            # Skip empty lines at the start
            if not formatted_lines and not line.strip():
                continue

            formatted_lines.append(line)

        # Add signature
        formatted_lines.append("")
        formatted_lines.append("---")
        formatted_lines.append("These operational rules are binding and must be followed.")

        return "\n".join(formatted_lines)

    def get_rules_metadata(self) -> Dict:
        """Get metadata about the loaded rules.

        Returns:
            Dictionary with rules metadata
        """
        if not self.rules_file.exists():
            return {
                "exists": False,
                "file": str(self.rules_file),
                "rules_loaded": 0,
                "hotload_enabled": True,
            }

        rules = self.load_rules()
        if not rules:
            return {
                "exists": True,
                "file": str(self.rules_file),
                "rules_loaded": 0,
                "hotload_enabled": True,
                "error": "Failed to load rules",
            }

        # Count sections by counting top-level headers
        lines = rules.splitlines()
        sections = sum(1 for line in lines if line.startswith("### "))

        return {
            "exists": True,
            "file": str(self.rules_file),
            "file_size": self.rules_file.stat().st_size,
            "last_modified": self.rules_file.stat().st_mtime,
            "rules_loaded": sections,
            "hotload_enabled": True,
            "cached": self._cached_rules is not None,
        }

    def watch_file(self, interval: float = 1.0):
        """Watch for file changes (generator for hotloading).

        Args:
            interval: Check interval in seconds

        Yields:
            True when file has changed, False otherwise
        """
        last_check = time.time()

        while True:
            now = time.time()
            if now - last_check >= interval:
                if self._should_reload():
                    yield True
                else:
                    yield False
                last_check = now
            time.sleep(0.1)

    def get_section(self, section_title: str) -> Optional[str]:
        """Extract a specific section from rules.

        Args:
            section_title: Title of section to extract (e.g., "Git Ignore Policy")

        Returns:
            Section content or None if not found
        """
        rules = self.load_rules(force_reload=True)
        if not rules:
            return None

        lines = rules.splitlines()
        section_lines = []
        in_section = False

        # Support both ## and ### header formats
        section_headers = [
            f"## {section_title}",
            f"### {section_title}"
        ]

        for line in lines:
            # Check if this line starts a section we're looking for
            if any(line.strip() == header for header in section_headers):
                in_section = True
                continue
            elif in_section and (line.startswith("##") or line.startswith("###")):
                # Next section at same or higher level
                break
            elif in_section:
                section_lines.append(line)

        return "\n".join(section_lines).strip() if section_lines else None


def create_system_prompt_with_rules(
    base_prompt: str,
    rules_loader: RulesLoader,
    custom_sections: Optional[List[str]] = None,
) -> str:
    """Create enhanced system prompt with loaded rules.

    Args:
        base_prompt: Base system prompt
        rules_loader: RulesLoader instance
        custom_sections: Optional list of specific sections to include

    Returns:
        Enhanced system prompt with rules appended
    """
    rules = rules_loader.load_rules()

    if not rules:
        return base_prompt

    # If specific sections requested, extract them
    if custom_sections:
        filtered_rules = []
        for section in custom_sections:
            section_content = rules_loader.get_section(section)
            if section_content:
                filtered_rules.append(f"### {section}")
                filtered_rules.append(section_content)

        if filtered_rules:
            rules = "\n".join([
                "# TeamADAPT Rules & Protocols",
                "",
                "The following rules, protocols, and best practices MUST be followed:",
                "",
                *filtered_rules,
            ])

    return f"""{base_prompt}

---

{rules}
"""
