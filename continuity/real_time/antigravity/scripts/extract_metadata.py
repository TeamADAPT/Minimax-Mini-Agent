#!/usr/bin/env python3
"""
Antigravity Conversation Metadata Extractor
Extracts structured metadata from JSONL conversation files
"""

import json
import re
import sys
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging for both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ConversationMetadataExtractor:
    """Extract comprehensive metadata from antigravity conversation files"""

    def __init__(self, extract_full_text: bool = False):
        self.extract_full_text = extract_full_text
        self.stats = {
            'files_processed': 0,
            'files_with_antigravity': 0,
            'total_messages': 0,
            'api_methods_found': 0,
            'security_warnings_found': 0
        }

    def extract_api_methods(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract API access methods from conversation content
        Returns list of method dictionaries with protocol, port, access level
        """
        methods = []
        content_lower = content.lower()

        # Chrome DevTools Protocol (CDP) - Port 9222
        cdp_patterns = [
            r'ChromeDevTools|chrome-devtools|CDP.*9222',
            r'remote-debugging-port=9222',
            r'localhost:9222|127\.0\.0\.1:9222',
            r'Chrome Developer Tools|chrome://inspect'
        ]

        if any(re.search(pattern, content, re.I) for pattern in cdp_patterns):
            methods.append({
                'name': 'ChromeDevTools',
                'protocol': 'CDP',
                'port': 9222,
                'access_level': 'dev_style',
                'description': 'Direct browser control via Chrome DevTools Protocol',
                'context': self._extract_context(content, 'chrome.*devtools|cdp|9222')
            })

        # Model Context Protocol (MCP) Server
        if re.search(r'MCP.*server|Model Context Protocol|@agentdeskai/browser-tools-mcp', content, re.I):
            methods.append({
                'name': 'McpServer',
                'protocol': 'MCP',
                'port': 'dynamic',
                'access_level': 'internal',
                'description': 'Model Context Protocol server for agent-browser communication',
                'context': self._extract_context(content, 'mcp.*server|model context protocol')
            })

        # Antigravity Proxy (MITM)
        if re.search(r'antigravity-proxy|mitmproxy|HTTP_PROXY.*8080', content, re.I):
            methods.append({
                'name': 'AntiGravityProxy',
                'protocol': 'HTTP',
                'port': 8080,
                'access_level': 'proxy',
                'description': 'MITM proxy for API call interception and debugging',
                'context': self._extract_context(content, 'antigravity-proxy|mitmproxy')
            })

        # Chrome Extension Bridge
        extension_patterns = [
            r'chrome.*extension|browser.*extension',
            r'Antigravity Browser Connector',
            r'\.gemini/antigravity-browser-profile'
        ]
        if any(re.search(pattern, content, re.I) for pattern in extension_patterns):
            methods.append({
                'name': 'ChromeExtension',
                'protocol': 'Extension',
                'port': 'N/A',
                'access_level': 'internal',
                'description': 'Chrome extension serving as browser automation bridge',
                'context': self._extract_context(content, 'chrome.*extension|browser.*extension')
            })

        # Port-based detection for other methods
        port_patterns = {
            9090: 'CascadeServer',
            9092: 'CascadeServerAlt',
            9101: 'MonitoringServer',
            4000: 'NoMachine',
            2024: 'LangGraphDev',
        }

        for port, method_name in port_patterns.items():
            if f':{port}' in content or f'port.*{port}' in content_lower:
                methods.append({
                    'name': method_name,
                    'protocol': 'TCP',
                    'port': port,
                    'access_level': 'internal',
                    'description': f'Internal service on port {port}',
                    'context': self._extract_context(content, f'port.*{port}|:{port}')
                })

        # Remove duplicates based on (name, port)
        unique_methods = {}
        for method in methods:
            key = (method['name'], method['port'])
            if key not in unique_methods:
                unique_methods[key] = method

        return list(unique_methods.values())

    def extract_security_warnings(self, content: str) -> List[Dict[str, Any]]:
        """Extract security vulnerabilities and warnings from content"""
        warnings = []

        # Critical vulnerabilities reported in Dec 2025
        security_patterns = {
            'data_exfiltration': {
                'patterns': [r'⚠️.*data exfiltration', r'data exfiltration', r'ignore.*\.gitignore', r'read.*\.env'],
                'severity': 'critical'
            },
            'prompt_injection': {
                'patterns': [r'prompt injection', r'browser content.*manipulate', r'injection attack'],
                'severity': 'critical'
            },
            'api_key_leak': {
                'patterns': [r'API key.*exposed', r'token.*compromised', r'credential.*leak'],
                'severity': 'high'
            },
            'backdoor_risk': {
                'patterns': [r'backdoor', r'mcp_config\.json.*exploit', r'configuration.*attack'],
                'severity': 'critical'
            },
            'port_conflicts': {
                'patterns': [r'port.*conflict', r'bind.*failed', r'address already in use'],
                'severity': 'medium'
            },
            'memory_exhaustion': {
                'patterns': [r'50GB.*allocation', r'out of memory', r'memory.*exhausted'],
                'severity': 'medium'
            }
        }

        for warning_type, config in security_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, content, re.I)
                for match in matches:
                    # Get surrounding context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].strip()

                    warnings.append({
                        'warning_type': warning_type,
                        'severity': config['severity'],
                        'pattern': pattern,
                        'match': match.group(),
                        'context': context,
                        'line': self._get_line_number(content, match.start())
                    })

        return warnings

    def _extract_context(self, content: str, pattern: str, window: int = 100) -> Optional[str]:
        """Extract context around a pattern match"""
        match = re.search(pattern, content, re.I)
        if not match:
            return None

        start = max(0, match.start() - window)
        end = min(len(content), match.end() + window)
        return content[start:end].strip()

    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a character position"""
        return content[:position].count('\n') + 1

    def categorize_conversation(self, content: str) -> Dict[str, Any]:
        """
        Five-dimensional categorization of conversations
        """
        categories = {
            'conversation_type': 'general',
            'api_access_style': [],
            'technical_focus': [],
            'resource_context': 'unknown'
        }

        content_lower = content.lower()

        # 1. Conversation Type
        if re.search(r'comprehensive report|technical review|executive summary', content_lower):
            categories['conversation_type'] = 'comprehensive_report'
        elif re.search(r'crash.*fix|stability.*fix|resolution.*plan', content_lower):
            categories['conversation_type'] = 'crash_resolution'
        elif re.search(r'agent.*research|investigation|analysis', content_lower):
            categories['conversation_type'] = 'agent_research'
        elif re.search(r'query|question|how.*access|can.*use', content_lower):
            categories['conversation_type'] = 'api_access_query'
        elif re.search(r'conversation.*track|database.*ingest|categoriz', content_lower):
            categories['conversation_type'] = 'tracking_infrastructure'

        # 2. API Access Style
        if re.search(r'chrome.*devtools|cdp|9222', content_lower):
            categories['api_access_style'].append('dev_style')
        if re.search(r'mcp.*server|model context protocol', content_lower):
            categories['api_access_style'].append('mcp_server')
        if re.search(r'proxy|mitm', content_lower):
            categories['api_access_style'].append('proxy')
        if re.search(r'extension|browser.*bridge', content_lower):
            categories['api_access_style'].append('chrome_extension')

        # 3. Technical Focus Areas
        focus_areas = {
            'api_access_methods': [r'api.*endpoint', r'curl', r'port.*\d+', r'localhost:\d+'],
            'crash_resolution': [r'zombie.*process', r'crash', r'segmentation.*fault', r'core.*dump'],
            'browser_integration': [r'chromium|chrome.*browser', r'dom.*manipulation', r'browser.*automation'],
            'security_analysis': [r'vulnerability', r'security', r'exfiltration', r'injection'],
            'agent_architecture': [r'agent.*manager', r'jetski', r'sub-agent', r'orchestrat'],
            'configuration_management': [r'startup.*script', r'environment.*variable', r'configuration'],
            'tracking_infrastructure': [r'conversation.*track', r'database.*schema', r'ingest', r'categoriz']
        }

        for focus, patterns in focus_areas.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    if focus not in categories['technical_focus']:
                        categories['technical_focus'].append(focus)
                    break

        # 4. Resource Context
        if re.search(r'64GB|38GB|50GB', content):
            categories['resource_context'] = 'high_resource'
        elif re.search(r'15GB|constrained|limited.*resource', content_lower):
            categories['resource_context'] = 'constrained'
        elif re.search(r'crash.*fix|stability.*issue|memory.*leak', content_lower):
            categories['resource_context'] = 'crash_recovery'
        elif re.search(r'multi.*service|concurrent|alongside', content_lower):
            categories['resource_context'] = 'multi_service'

        return categories

    def calculate_content_metrics(self, content: str, messages: List[Dict]) -> Dict[str, Any]:
        """Calculate various content metrics"""
        metrics = {
            'word_count': len(content.split()),
            'line_count': content.count('\n'),
            'message_count': len(messages),
            'has_code_examples': False,
            'has_security_warnings': False,
            'security_warning_count': 0
        }

        # Check for code examples
        code_indicators = [
            '```',
            'import ',
            'function ',
            'const ',
            'let ',
            'class ',
            'def ',
            'curl ',
            'psql ',
            'mongosh '
        ]

        metrics['has_code_examples'] = any(indicator in content for indicator in code_indicators)

        # Check for security warnings
        security_patterns = ['⚠️', 'WARNING', 'vulnerability', 'security risk', 'critical issue']
        for pattern in security_patterns:
            if pattern.lower() in content.lower():
                metrics['has_security_warnings'] = True
                metrics['security_warning_count'] += content.lower().count(pattern.lower())

        return metrics

    def extract_metadata(self, jsonl_file: Path, extract_text: bool = False) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from a JSONL conversation file
        """
        metadata = {
            'session_id': None,
            'file_path': str(jsonl_file),
            'file_name': jsonl_file.name,
            'file_hash': self._file_hash(jsonl_file),
            'messages_count': 0,
            'api_methods': [],
            'security_warnings': [],
            'created_at': None,
            'updated_at': None,
            'content_summary': '',
        }

        messages = []
        all_content = []

        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        metadata['messages_count'] += 1
                        self.stats['total_messages'] += 1

                        # Extract session ID from first valid message
                        if metadata['session_id'] is None:
                            metadata['session_id'] = self._extract_session_id(data, line_num)

                        # Extract timestamp
                        timestamp = self._extract_timestamp(data, line_num)
                        if timestamp:
                            if metadata['created_at'] is None:
                                metadata['created_at'] = timestamp
                            metadata['updated_at'] = timestamp

                        # Extract content
                        content = self._extract_content(data, line_num)
                        if content:
                            messages.append({
                                'line': line_num,
                                'timestamp': timestamp,
                                'content': content
                            })
                            all_content.append(content)

                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {line_num}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error reading file {jsonl_file}: {e}")
            raise

        # Check if this is actually about antigravity
        full_text = "\n".join(all_content)
        if 'antigravity' not in full_text.lower():
            logger.debug(f"File {jsonl_file} does not contain antigravity content")
            return None

        self.stats['files_with_antigravity'] += 1

        # Generate summary
        if full_text:
            metadata['full_text'] = full_text if extract_text else None
            metadata['content_summary'] = full_text[:800] + "..." if len(full_text) > 800 else full_text
            metadata.update(self.calculate_content_metrics(full_text, messages))

            # Extract API methods
            methods = self.extract_api_methods(full_text)
            if methods:
                metadata['api_methods'] = methods
                metadata['api_methods_count'] = len(methods)
                self.stats['api_methods_found'] += len(methods)

            # Extract security warnings
            warnings = self.extract_security_warnings(full_text)
            if warnings:
                metadata['security_warnings'] = warnings
                metadata['security_warning_count'] = len(warnings)
                self.stats['security_warnings_found'] += len(warnings)

            # Categorize conversation
            categories = self.categorize_conversation(full_text)
            metadata.update(categories)

        self.stats['files_processed'] += 1
        return metadata

    def _extract_session_id(self, data: Dict, line_num: int) -> Optional[str]:
        """Extract session ID from conversation data"""
        try:
            if 'sessionId' in data:
                return data['sessionId']
            elif 'message' in data and isinstance(data['message'], dict):
                if 'sessionId' in data['message']:
                    return data['message']['sessionId']
        except Exception as e:
            logger.warning(f"Could not extract session ID from line {line_num}: {e}")
        return None

    def _extract_timestamp(self, data: Dict, line_num: int) -> Optional[str]:
        """Extract timestamp from conversation data"""
        try:
            # Try multiple timestamp field locations
            if 'timestamp' in data:
                return data['timestamp']
            elif 'message' in data and isinstance(data['message'], dict) and 'timestamp' in data['message']:
                return data['message']['timestamp']
        except Exception as e:
            logger.warning(f"Could not extract timestamp from line {line_num}: {e}")
        return None

    def _extract_content(self, data: Dict, line_num: int) -> Optional[str]:
        """Extract message content from conversation data"""
        try:
            content = ""

            if 'message' in data and isinstance(data['message'], dict):
                message = data['message']

                # Handle different content formats
                if 'content' in message:
                    content = str(message['content'])
                elif 'role' in message:
                    # Convert entire message to string if it has content
                    content = str(message)

                # Extract from tool results if present
                if 'tool_result' in str(content) or 'tool_use' in str(content):
                    content = str(data)

            return content if content else None

        except Exception as e:
            logger.warning(f"Could not extract content from line {line_num}: {e}")
            return None

    def _file_hash(self, filepath: Path) -> Optional[str]:
        """Calculate MD5 hash of file for change detection"""
        try:
            hasher = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Could not hash file {filepath}: {e}")
            return None

    def print_stats(self):
        """Print extraction statistics"""
        print("\n" + "=" * 60)
        print("Extraction Statistics")
        print("=" * 60)
        print(f"Files processed:     {self.stats['files_processed']}")
        print(f"Files with antigravity: {self.stats['files_with_antigravity']}")
        print(f"Total messages:      {self.stats['total_messages']}")
        print(f"API methods found:   {self.stats['api_methods_found']}")
        print(f"Security warnings:   {self.stats['security_warnings_found']}")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Extract metadata from antigravity conversation files')
    parser.add_argument('--input', required=True, help='Input JSONL file or directory')
    parser.add_argument('--output', required=True, help='Output JSON file or directory')
    parser.add_argument('--extract-text', action='store_true', help='Extract full conversation text')
    parser.add_argument('--extract-api-methods', action='store_true', help='Extract API method information')
    parser.add_argument('--log', help='Log file path')
    parser.add_argument('--stats', action='store_true', help='Print extraction statistics')

    args = parser.parse_args()

    # Set up file logging if specified
    if args.log:
        log_dir = Path(args.log).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(args.log)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    extractor = ConversationMetadataExtractor(extract_full_text=args.extract_text)

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Process single file
    if input_path.is_file():
        logger.info(f"Processing file: {input_path}")

        metadata = extractor.extract_metadata(input_path, extract_text=args.extract_text)

        if metadata:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

            logger.info(f"Metadata written to: {output_path}")
            logger.info(f"Session ID: {metadata['session_id']}")
            logger.info(f"API methods: {len(metadata.get('api_methods', []))}")
            logger.info(f"Security warnings: {metadata.get('security_warning_count', 0)}")
        else:
            logger.warning(f"No metadata extracted from {input_path}")

    # Process directory
    elif input_path.is_dir():
        logger.info(f"Processing directory: {input_path}")
        output_path.mkdir(parents=True, exist_ok=True)

        jsonl_files = list(input_path.rglob("*.jsonl"))
        logger.info(f"Found {len(jsonl_files)} JSONL files")

        for i, jsonl_file in enumerate(jsonl_files, 1):
            logger.info(f"[{i}/{len(jsonl_files)}] Processing: {jsonl_file}")

            try:
                metadata = extractor.extract_metadata(jsonl_file, extract_text=args.extract_text)

                if metadata:
                    output_file = output_path / f"{jsonl_file.name}.json"
                    with open(output_file, 'w') as f:
                        json.dump(metadata, f, indent=2, default=str)
                    logger.info(f"  ✓ Extracted: {metadata['session_id']}")
                else:
                    logger.info(f"  - Skipped (no antigravity content)")

            except Exception as e:
                logger.error(f"  ✗ Error processing {jsonl_file}: {e}")
                continue

    else:
        logger.error(f"Invalid input path: {input_path}")
        sys.exit(1)

    if args.stats:
        extractor.print_stats()

if __name__ == "__main__":
    main()
