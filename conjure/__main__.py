#!/usr/bin/env python3
"""
Command-line interface for conjure.
"""
import sys
import json
from pathlib import Path
from typing import Optional
import typer

try:
    from .conjure import Conjure
    from .utilities import setup_warning_filter
except ImportError:
    from conjure import Conjure
    from utilities import setup_warning_filter

# Set up rich warning formatting
setup_warning_filter()


app = typer.Typer()

@app.command()
def main(
    file_path: Path = typer.Argument(..., help="Path to the input survey data file"),
    json_gz_filename: Optional[str] = typer.Option(None, "--json-gz-filename", help="Save results to compressed JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """
    Convert survey data files into EDSL objects.
    
    Supports .csv, .sav (SPSS), and .dta (Stata) file formats.
    
    By default, outputs results as JSON to stdout. Use --json-gz-filename to save to a compressed file.
    """
    try:
        if verbose:
            typer.echo(f"Processing file: {file_path}")
            typer.echo(f"File type: {file_path.suffix}")
        
        # Create conjure instance
        conjure_instance = Conjure(str(file_path))
        
        if verbose:
            typer.echo(f"Created conjure instance of type: {type(conjure_instance).__name__}")
        
        # Get results
        results = conjure_instance.to_results()
        
        # Handle output
        if json_gz_filename:
            # Save to compressed JSON file
            results.save(json_gz_filename)
            if verbose:
                typer.echo(f"✓ Results saved to {json_gz_filename}")
        else:
            # Output JSON to stdout
            results_dict = results.to_dict()
            print(json.dumps(results_dict, indent=2))
        
        if verbose:
            typer.echo("✓ File processed successfully")
        
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    app()