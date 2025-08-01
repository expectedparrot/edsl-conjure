#!/usr/bin/env python3
"""
Command-line interface for conjure.
"""
import sys
import json
import pandas as pd
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
    silent: bool = typer.Option(False, "--silent", "-s", help="Disable verbose output"),
    sample: Optional[int] = typer.Option(None, "--sample", help="Sample size to use instead of processing all agents"),
    data_dictionary_csv: Optional[Path] = typer.Option(None, "--data-dictionary-csv", help="Path to CSV file containing question names and texts"),
    question_name_column: str = typer.Option("question_name", "--question-name-column", help="Column name or index (0-based) for question names in data dictionary CSV"),
    question_text_column: str = typer.Option("question_text", "--question-text-column", help="Column name or index (0-based) for question texts in data dictionary CSV")
):
    """
    Convert survey data files into EDSL objects.
    
    Supports .csv, .sav (SPSS), and .dta (Stata) file formats.
    Can read from file path or stdin (pipe input).
    
    By default, outputs results as JSON to stdout. Use --json-gz-filename to save to a compressed file.
    
    EXAMPLE USAGE:
    
    Basic usage with CSV file:
        conjure survey_data.csv
    
    Using data dictionary to map question names to readable text:
        conjure examples/pittsburgh_av/avsurvey2019data.csv \\
            --data-dictionary-csv examples/pittsburgh_av/avsurvey2019datadictionary.csv \\
            --question-name-column 0 --question-text-column 1 | edsl
    
    Example data file (avsurvey2019data.csv):
        RespondentID,StartDate,EndDate,FamiliarityNews,FamiliarityTech,SharedCyclist...
        10505419886,2/2/2019,2/2/2019,To a moderate extent,Somewhat familiar,Yes...
        10505138734,2/2/2019,2/2/2019,To a moderate extent,Somewhat familiar,Yes...
    
    Example data dictionary (avsurvey2019datadictionary.csv):
        FieldName,Description or Question,Range of Responses
        RespondentID,Respondent ID,N/A
        StartDate,Date survey started,N/A
        FamiliarityNews,To what extent have you been paying attention to the subject of AVs in the news?,To a large extent; to a moderate extent; to some extent; to little extent; not at all
    
    The --question-name-column and --question-text-column can be specified by:
    - Column name: --question-name-column "FieldName"
    - Column index (0-based): --question-name-column 0
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
            
            if not silent:
                console.print("[blue]Processing data from stdin[/blue]")
                console.print(f"[dim]Temporary file: {file_path}[/dim]")
        else:
            cleanup_temp_file = False
        
        if not silent:
            console.print(f"[blue]Processing file:[/blue] {file_path}")
            console.print(f"[dim]File type: {file_path.suffix}[/dim]")
        
        # Load question texts from data dictionary CSV if provided
        question_texts = None
        if data_dictionary_csv:
            try:
                if not silent:
                    console.print(f"[blue]Loading data dictionary:[/blue] {data_dictionary_csv}")
                
                dict_df = pd.read_csv(data_dictionary_csv, encoding='latin-1')
                
                if not silent:
                    console.print(f"[dim]Data dictionary shape: {dict_df.shape}[/dim]")
                    console.print(f"[dim]Data dictionary columns: {list(dict_df.columns)}[/dim]")
                
                # Handle column specification by name or index
                def get_column_data(df, column_spec):
                    if column_spec.isdigit():
                        col_index = int(column_spec)
                        if col_index < 0 or col_index >= len(df.columns):
                            raise ValueError(f"Column index {col_index} out of range (0-{len(df.columns)-1})")
                        return df.iloc[:, col_index]
                    else:
                        if column_spec not in df.columns:
                            raise ValueError(f"Column '{column_spec}' not found in data dictionary CSV")
                        return df[column_spec]
                
                # Get column data by name or index
                question_name_data = get_column_data(dict_df, question_name_column)
                question_text_data = get_column_data(dict_df, question_text_column)
                
                # Create mapping from question names to question texts, filtering out NaN values
                # Use lowercase keys for case-insensitive matching
                question_name_to_text = {}
                for name, text in zip(question_name_data, question_text_data):
                    # Skip rows where either name or text is NaN/None
                    if pd.notna(name) and pd.notna(text):
                        question_name_to_text[str(name).lower()] = str(text)
                
                if not silent:
                    console.print(f"[dim]Loaded {len(question_name_to_text)} question mappings[/dim]")
                
                # Store the mapping for later use
                question_texts = question_name_to_text
                
            except Exception as e:
                console.print(f"[red]Error loading data dictionary:[/red] {e}")
                sys.exit(1)
        
        # Create conjure instance
        conjure_instance = Conjure(str(file_path), question_names_to_question_text=question_texts)
        
        # Add diagnostics about data dictionary usage
        if data_dictionary_csv and question_texts and not silent:
            # Get actual column names from the data file (convert to lowercase for case-insensitive matching)
            actual_columns = set(name.lower() for name in conjure_instance.question_names)
            dict_questions = set(question_texts.keys())  # Already lowercase from above
            
            matched_questions = actual_columns.intersection(dict_questions)
            unmatched_from_dict = dict_questions - actual_columns
            unmatched_from_data = actual_columns - dict_questions
            
            console.print(f"[cyan]Data Dictionary Usage Diagnostics:[/cyan]")
            console.print(f"  📊 Total questions in data dictionary: {len(dict_questions)}")
            console.print(f"  📋 Total columns in data file: {len(actual_columns)}")
            console.print(f"  ✅ Matched questions: {len(matched_questions)}")
            console.print(f"  ❌ Unmatched from dictionary: {len(unmatched_from_dict)}")
            console.print(f"  ❓ Unmatched from data: {len(unmatched_from_data)}")
            
            if unmatched_from_dict:
                console.print(f"  [dim]Dictionary questions not found in data:[/dim]")
                for q in sorted(unmatched_from_dict):
                    console.print(f"    • {q}")
            
            if unmatched_from_data:
                console.print(f"  [dim]Data columns not found in dictionary:[/dim]")
                for q in sorted(unmatched_from_data):
                    console.print(f"    • {q}")
                    
            if matched_questions:
                console.print(f"  [dim]Successfully matched questions:[/dim]")
                for q in sorted(matched_questions):
                    console.print(f"    • {q}")
                    
            match_rate = (len(matched_questions) / len(dict_questions)) * 100 if dict_questions else 0
            console.print(f"  📈 Dictionary match rate: {match_rate:.1f}%")
        elif data_dictionary_csv and not silent:
            if not question_texts:
                console.print(f"[yellow]Warning: Data dictionary CSV was provided but no question texts were loaded[/yellow]")
        
        # Store verbose flag for later use
        conjure_instance._verbose = not silent
        
        if not silent:
            console.print(f"[dim]Created conjure instance of type: {type(conjure_instance).__name__}[/dim]")
        
        # Get results
        results = conjure_instance.to_results(verbose=not silent, sample_size=sample)
        
        # Handle output
        if json_gz_filename:
            # Save to compressed JSON file
            results.save(json_gz_filename)
            if not silent:
                console.print(f"[green]✓[/green] Results saved to {json_gz_filename}")
        else:
            # Output JSON to stdout
            results_dict = results.to_dict(add_edsl_version=True)
            print(json.dumps(results_dict, indent=2))
        
        if not silent:
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