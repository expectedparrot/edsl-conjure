# CLAUDE.md - Guidelines for Conjure Codebase

## Build & Test Commands
- Run doctests in a file: `python -m doctest filename.py`
- Run doctests with verbose output: `python -m doctest filename.py -v`
- Run module directly (also runs tests): `python filename.py`
- Test question editing functionality: `python test_question_editing.py`

## Question Editing Features
Conjure now supports editing questions before agents are built. There are two main approaches:

### Approach 1: Edit at Instantiation
Pass a `question_edits` function when creating a Conjure instance:

```python
def apply_survey_edits(survey_data):
    return (survey_data
        .with_edited_question('confidence_topic_highest2', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
        .with_edited_question('response_characters_less2', {'question_type': 'free_text'}, pop_fields=['question_options'])
        .with_renamed_question('confidence_topic_highest2', 'long_run_us_fiscal_sustainability_confidence')
        .drop('last_name', 'first_name')
    )

# Apply edits at instantiation
focal_survey = Conjure("datafile.csv", question_edits=apply_survey_edits)
survey = focal_survey.to_survey()  # Survey is already edited
results = focal_survey.to_results()  # Results use edited questions
```

### Approach 2: Fluent Chaining After Creation
Create a Conjure instance, then use fluent chaining for complex edits:

```python
# Fluent chaining - matches your exact workflow pattern!
focal_survey = (Conjure("datafile.csv")
    .edit_question('confidence_topic_highest2', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
    .edit_question('response_characters_less2', {'question_type': 'free_text'}, pop_fields=['question_options'])
    .edit_question('confidence_topic_highest', {'question_options': [1,2,3,4,5,6,7,8,9,10]})
    .edit_question('response_characters_less', {'question_type': 'free_text'}, pop_fields=['question_options'])
    .rename_question('confidence_topic_highest2', 'long_run_us_fiscal_sustainability_confidence')
    .drop_questions('last_name', 'first_name')
)

# Or use apply_question_edits for reusable edit functions
focal_survey.apply_question_edits(apply_survey_edits)

# Now call analysis methods with edited questions
survey = focal_survey.to_survey()
results = focal_survey.to_results()
```

### Functional Methods (Return New Instances):
- `with_edited_question(question_name, edits, pop_fields=None)`: Edit question attributes
- `with_renamed_question(old_name, new_name)`: Rename a question
- `drop(*question_names)`: Remove questions

### In-Place Methods (Modify Current Instance) - All Chainable/Fluent:
- `edit_question(question_name, edits, pop_fields=None)`: Edit question attributes in-place
- `rename_question(old_name, new_name)`: Rename a question in-place  
- `drop_questions(*question_names)`: Remove questions in-place
- `apply_question_edits(edit_function)`: Apply a complex editing function in-place

**Note**: All in-place methods return `self` for fluent chaining, allowing you to write clean, readable multi-step transformations exactly like your original workflow pattern.

### Supported Edits:
- `question_options`: Change multiple choice options
- `question_type`: Change question type (e.g., 'multiple_choice' to 'free_text')
- `question_text`: Modify the question text
- `pop_fields`: Remove attributes like 'question_options'

## Code Style Guidelines
- **Imports**: Standard library → Third-party → Project imports, grouped with blank lines
- **Formatting**: 4-space indentation, triple quotes for docstrings
- **Types**: Use typing module (List, Dict, Optional, Union, etc.)
- **Naming**: CamelCase classes, snake_case methods/variables, UPPER_CASE constants
- **Error Handling**: Use specific exceptions with descriptive messages
- **Docstrings**: Include examples, parameter descriptions, and doctests
- **Design Patterns**: Use mixins for shared functionality, ABC for interfaces
- **Documentation**: Write docstrings with examples as doctests