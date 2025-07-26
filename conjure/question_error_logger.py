"""
Question error logging system for conjure.
Collects question processing errors and provides clean user feedback.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class QuestionErrorLogger:
    """Centralized logging system for question processing errors."""
    
    def __init__(self, datafile_name: str, verbose: bool = False):
        self.datafile_name = datafile_name
        self.verbose = verbose
        self.errors: List[Dict[str, Any]] = []
        self.console = Console(stderr=True)
        
        # Create logs directory if it doesn't exist
        self.log_dir = Path("conjure_logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = Path(datafile_name).stem.replace(" ", "_")
        self.log_file = self.log_dir / f"question_errors_{safe_filename}_{timestamp}.log"
        
        # Initialize log file
        with open(self.log_file, 'w') as f:
            f.write(f"Question Processing Error Log\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Data file: {datafile_name}\n")
            f.write(f"{'='*80}\n\n")
    
    def log_question_error(self, question_name: str, error_type: str, details: str, exception: Exception = None):
        """Log a question processing error."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'question_name': question_name,
            'error_type': error_type,
            'details': details,
            'exception': str(exception) if exception else None
        }
        
        self.errors.append(error_entry)
        
        # Write to log file immediately
        with open(self.log_file, 'a') as f:
            f.write(f"[{error_entry['timestamp']}] Question: {question_name}\n")
            f.write(f"Error Type: {error_type}\n")
            f.write(f"Details: {details}\n")
            if exception:
                f.write(f"Exception: {exception}\n")
            f.write("-" * 80 + "\n\n")
    
    def log_insufficient_options_error(self, question_name: str, options_info: str):
        """Log an insufficient options error specifically."""
        self.log_question_error(
            question_name=question_name,
            error_type="Insufficient Options",
            details=f"Too few question options (got {options_info}). Question will be omitted."
        )
    
    def log_creation_error(self, question_name: str, exception: Exception):
        """Log a question creation error."""
        self.log_question_error(
            question_name=question_name,
            error_type="Creation Failed",
            details="Failed to create question object",
            exception=exception
        )
    
    def display_summary(self):
        """Display a clean summary of errors to the user."""
        if not self.errors:
            return
        
        # Group errors by type
        error_by_type = {}
        for error in self.errors:
            error_type = error['error_type']
            if error_type not in error_by_type:
                error_by_type[error_type] = []
            error_by_type[error_type].append(error)
        
        # Create summary table
        table = Table(title="Question Processing Issues", show_header=True, header_style="bold magenta")
        table.add_column("Issue Type", style="cyan", no_wrap=True)
        table.add_column("Count", style="bold red", justify="right")
        table.add_column("Examples", style="dim")
        
        total_errors = len(self.errors)
        
        for error_type, type_errors in error_by_type.items():
            count = len(type_errors)
            # Show first few question names as examples
            examples = [e['question_name'] for e in type_errors[:3]]
            if count > 3:
                examples.append(f"... and {count - 3} more")
            example_text = ", ".join(examples)
            
            table.add_row(error_type, str(count), example_text)
        
        # Create summary panel
        summary_text = f"[bold red]{total_errors}[/bold red] questions had processing issues and were omitted"
        if total_errors > 0:
            log_info = f"\n[dim]Detailed error log: {self.log_file}[/dim]"
            summary_text += log_info
        
        panel = Panel(
            summary_text,
            title="⚠️  Question Processing Summary",
            border_style="yellow",
            expand=False
        )
        
        self.console.print()
        self.console.print(panel)
        if total_errors > 0:
            self.console.print(table)
        self.console.print()
    
    def get_error_count(self) -> int:
        """Get the total number of errors logged."""
        return len(self.errors)
    
    def get_failed_questions(self) -> List[str]:
        """Get list of question names that failed."""
        return [error['question_name'] for error in self.errors]
    
    def has_errors(self) -> bool:
        """Check if any errors were logged."""
        return len(self.errors) > 0


# Global logger instance - will be set by the main process
_global_logger: QuestionErrorLogger = None


def set_global_logger(logger: QuestionErrorLogger):
    """Set the global logger instance."""
    global _global_logger
    _global_logger = logger


def get_global_logger() -> QuestionErrorLogger:
    """Get the global logger instance."""
    return _global_logger


def log_question_error(question_name: str, error_type: str, details: str, exception: Exception = None):
    """Log a question error using the global logger."""
    if _global_logger:
        _global_logger.log_question_error(question_name, error_type, details, exception)


def log_insufficient_options_error(question_name: str, options_info: str):
    """Log an insufficient options error using the global logger."""
    if _global_logger:
        _global_logger.log_insufficient_options_error(question_name, options_info)


def log_creation_error(question_name: str, exception: Exception):
    """Log a question creation error using the global logger."""
    if _global_logger:
        _global_logger.log_creation_error(question_name, exception)