"""
TOML Parser for Minecraft Server Configuration
A simple TOML parser implementation for parsing configuration files.
"""

import re
import json
from typing import Dict, Any, Union, List
from datetime import datetime


class TOMLParseError(Exception):
    """Exception raised when TOML parsing fails"""
    pass


class TOMLParser:
    """A simple TOML parser implementation"""

    def __init__(self):
        self.data = {}
        self.current_table = self.data
        self.table_path = []

    def parse_file(self, filename: str) -> Dict[str, Any]:
        """Parse a TOML file and return the parsed data"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            return self.parse_string(content)
        except FileNotFoundError:
            raise TOMLParseError(f"File not found: {filename}")
        except Exception as e:
            raise TOMLParseError(f"Error reading file {filename}: {str(e)}")

    def parse_string(self, content: str) -> Dict[str, Any]:
        """Parse a TOML string and return the parsed data"""
        self.data = {}
        self.current_table = self.data
        self.table_path = []

        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            try:
                self._parse_line(line.strip())
            except Exception as e:
                raise TOMLParseError(f"Error on line {line_num}: {str(e)}")

        return self.data

    def _parse_line(self, line: str):
        """Parse a single line of TOML"""
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            return

        # Handle table headers [table] or [[array_table]]
        if line.startswith('['):
            self._parse_table_header(line)
            return

        # Handle key-value pairs
        if '=' in line:
            self._parse_key_value(line)
            return

        raise TOMLParseError(f"Invalid syntax: {line}")

    def _parse_table_header(self, line: str):
        """Parse table headers like [server] or [[database]]"""
        if line.startswith('[[') and line.endswith(']]'):
            # Array of tables
            table_name = line[2:-2].strip()
            self._create_array_table(table_name)
        elif line.startswith('[') and line.endswith(']'):
            # Regular table
            table_name = line[1:-1].strip()
            self._create_table(table_name)
        else:
            raise TOMLParseError(f"Invalid table header: {line}")

    def _create_table(self, table_name: str):
        """Create a new table"""
        if '.' in table_name:
            # Nested table like [server.database]
            parts = table_name.split('.')
        else:
            parts = [table_name]

        # Navigate to the correct position in the data structure
        current = self.data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Create the final table
        last_part = parts[-1]
        if last_part not in current:
            current[last_part] = {}

        self.current_table = current[last_part]
        self.table_path = parts

    def _create_array_table(self, table_name: str):
        """Create an array of tables"""
        if '.' in table_name:
            parts = table_name.split('.')
        else:
            parts = [table_name]

        # Navigate to the correct position
        current = self.data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Create or append to array
        last_part = parts[-1]
        if last_part not in current:
            current[last_part] = []

        # Add new table to array
        new_table = {}
        current[last_part].append(new_table)
        self.current_table = new_table
        self.table_path = parts

    def _parse_key_value(self, line: str):
        """Parse key-value pairs"""
        # Split on the first '=' only
        parts = line.split('=', 1)
        if len(parts) != 2:
            raise TOMLParseError(f"Invalid key-value pair: {line}")

        key = parts[0].strip()
        value_str = parts[1].strip()

        # Parse the value
        value = self._parse_value(value_str)

        # Handle dotted keys like server.port = 25565
        if '.' in key:
            self._set_dotted_key(key, value)
        else:
            self.current_table[key] = value

    def _set_dotted_key(self, key: str, value: Any):
        """Set a value using a dotted key path"""
        parts = key.split('.')
        current = self.current_table

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    def _parse_value(self, value_str: str) -> Any:
        """Parse a value string and return the appropriate Python type"""
        value_str = value_str.strip()

        # String values
        if value_str.startswith('"') and value_str.endswith('"'):
            return self._parse_string_value(value_str)
        elif value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]  # Literal string

        # Boolean values
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False

        # Array values
        if value_str.startswith('[') and value_str.endswith(']'):
            return self._parse_array(value_str)

        # Inline table values
        if value_str.startswith('{') and value_str.endswith('}'):
            return self._parse_inline_table(value_str)

        # Numeric values
        try:
            # Try integer first
            if '.' not in value_str and 'e' not in value_str.lower():
                return int(value_str)
            else:
                return float(value_str)
        except ValueError:
            pass

        # If nothing else matches, treat as unquoted string (not standard TOML)
        return value_str

    def _parse_string_value(self, value_str: str) -> str:
        """Parse a quoted string value, handling escape sequences"""
        content = value_str[1:-1]  # Remove quotes

        # Handle escape sequences
        escape_map = {
            '\\n': '\n',
            '\\t': '\t',
            '\\r': '\r',
            '\\"': '"',
            '\\\\': '\\',
        }

        for escape, replacement in escape_map.items():
            content = content.replace(escape, replacement)

        return content

    def _parse_array(self, array_str: str) -> List[Any]:
        """Parse an array value"""
        content = array_str[1:-1].strip()  # Remove brackets

        if not content:
            return []

        # Simple comma-separated parsing
        items = []
        current_item = ""
        in_quotes = False
        bracket_depth = 0

        for char in content:
            if char == '"' and (not current_item or current_item[-1] != '\\'):
                in_quotes = not in_quotes
            elif char in '[{' and not in_quotes:
                bracket_depth += 1
            elif char in ']}' and not in_quotes:
                bracket_depth -= 1

            if char == ',' and not in_quotes and bracket_depth == 0:
                items.append(self._parse_value(current_item.strip()))
                current_item = ""
            else:
                current_item += char

        # Add the last item
        if current_item.strip():
            items.append(self._parse_value(current_item.strip()))

        return items

    def _parse_inline_table(self, table_str: str) -> Dict[str, Any]:
        """Parse an inline table value"""
        content = table_str[1:-1].strip()  # Remove braces

        if not content:
            return {}

        result = {}
        current_pair = ""
        in_quotes = False
        bracket_depth = 0

        for char in content:
            if char == '"' and (not current_pair or current_pair[-1] != '\\'):
                in_quotes = not in_quotes
            elif char in '[{' and not in_quotes:
                bracket_depth += 1
            elif char in ']}' and not in_quotes:
                bracket_depth -= 1

            if char == ',' and not in_quotes and bracket_depth == 0:
                key, value = current_pair.split('=', 1)
                result[key.strip()] = self._parse_value(value.strip())
                current_pair = ""
            else:
                current_pair += char

        # Add the last pair
        if current_pair.strip():
            key, value = current_pair.split('=', 1)
            result[key.strip()] = self._parse_value(value.strip())

        return result


def parse_toml_file(filename: str) -> Dict[str, Any]:
    """Convenience function to parse a TOML file"""
    parser = TOMLParser()
    return parser.parse_file(filename)


def parse_toml_string(content: str) -> Dict[str, Any]:
    """Convenience function to parse a TOML string"""
    parser = TOMLParser()
    return parser.parse_string(content)


# Example usage
if __name__ == "__main__":
    # Example TOML content
    example_toml = """
    # Server configuration
    [server]
    host = "0.0.0.0"
    port = 25565
    max_players = 20

    [server.messages]
    motd = "§cLe serveur est actuellement fermé."
    kick_message = "§cDésolé, le serveur est en maintenance.\\nRevenez plus tard !"

    [minecraft]
    version = "Maintenance"
    protocol_version = 47

    # Features
    features = ["maintenance_mode", "custom_motd", "player_limit"]

    # Player settings
    [players]
    whitelist = false
    ops = ["admin", "moderator"]

    [[database]]
    name = "main"
    type = "sqlite"
    path = "data.db"
    """

    try:
        data = parse_toml_string(example_toml)
        print("Parsed TOML data:")
        print(json.dumps(data, indent=2))
    except TOMLParseError as e:
        print(f"TOML parsing error: {e}")
