#!/usr/bin/env python3
"""
Command-line interface for conjure.
"""
import sys
import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.text import Text

try:
    from .conjure import Conjure
    from .utilities import setup_warning_filter
except ImportError:
    from conjure import Conjure
    from utilities import setup_warning_filter

# Set up rich warning formatting
setup_warning_filter()

# Create rich console for stderr output
console = Console(stderr=True)

app = typer.Typer()

@app.command()
def main(
    file_path: Optional[Path] = typer.Argument(None, help="Path to the input survey data file (or stdin if not provided)"),
    json_gz_filename: Optional[str] = typer.Option(None, "--json-gz-filename", help="Save results to compressed JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """
    Convert survey data files into EDSL objects.
    
    Supports .csv, .sav (SPSS), and .dta (Stata) file formats.
    Can read from file path or stdin (pipe input).
    
    By default, outputs results as JSON to stdout. Use --json-gz-filename to save to a compressed file.
    """
    try:
        # Handle stdin input
        if file_path is None:
            # Check if stdin has data
            if sys.stdin.isatty():
                console.print("[red]Error:[/red] No file path provided and no data piped to stdin")
                sys.exit(1)
            
            # Read from stdin
            import tempfile
            import os
            
            stdin_data = sys.stdin.read()
            if not stdin_data.strip():
                console.print("[red]Error:[/red] No data received from stdin")
                sys.exit(1)
            
            # Create a temporary file to store stdin data
            # We need to determine the file type from the data content
            # For now, assume CSV if no extension can be determined
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            temp_file.write(stdin_data)
            temp_file.flush()
            temp_file.close()
            
            file_path = Path(temp_file.name)
            cleanup_temp_file = True
            
            if verbose:
                console.print("[blue]Processing data from stdin[/blue]")
                console.print(f"[dim]Temporary file: {file_path}[/dim]")
        else:
            cleanup_temp_file = False
        
        if verbose:
            console.print(f"[blue]Processing file:[/blue] {file_path}")
            console.print(f"[dim]File type: {file_path.suffix}[/dim]")
        
        # Create conjure instance
        conjure_instance = Conjure(str(file_path))
        
        if verbose:
            console.print(f"[dim]Created conjure instance of type: {type(conjure_instance).__name__}[/dim]")
        
        # Get results
        results = conjure_instance.to_results()
        
        # Handle output
        if json_gz_filename:
            # Save to compressed JSON file
            results.save(json_gz_filename)
            if verbose:
                console.print(f"[green]✓[/green] Results saved to {json_gz_filename}")
        else:
            # Output JSON to stdout
            results_dict = results.to_dict(add_edsl_version=True)
            print(json.dumps(results_dict, indent=2))
        
        if verbose:
            console.print("[green]✓[/green] File processed successfully")
        
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)
    finally:
        # Clean up temporary file if created
        if 'cleanup_temp_file' in locals() and cleanup_temp_file:
            import os
            try:
                os.unlink(file_path)
            except OSError:
                pass


if __name__ == '__main__':
    app()