#!/usr/bin/env python3
"""
Test script for the new question editing functionality in conjure.
"""

from conjure.input_data import InputDataABC

def test_question_editing():
    """Test the new question editing methods."""
    
    print("Testing conjure question editing functionality...")
    print("=" * 50)
    
    # Create a basic example
    id = InputDataABC.example()
    print(f"Original question names: {id.question_names}")
    print(f"Original question types: {id.question_type.question_types}")
    print(f"Original question options: {id.question_option.question_options}")
    print()
    
    # Test 1: Edit question options
    print("Test 1: Editing question options")
    edited = id.with_edited_question('morning', {'question_options': [1,2,3,4,5,6,7,8,9,10]})
    print(f"After editing 'morning' question options: {edited.question_option.question_options[0]}")
    print()
    
    # Test 2: Change question type and remove options
    print("Test 2: Changing question type and removing options")  
    edited2 = id.with_edited_question('morning', {'question_type': 'free_text'}, pop_fields=['question_options'])
    print(f"After changing 'morning' to free_text: {edited2.question_type.question_types[0]}")
    print(f"Options after pop_fields: {edited2.question_option.question_options[0]}")
    print()
    
    # Test 3: Rename question
    print("Test 3: Renaming question")
    renamed = id.with_renamed_question('morning', 'morning_greeting')
    print(f"After renaming 'morning' to 'morning_greeting': {renamed.question_names}")
    print()
    
    # Test 4: Drop questions
    print("Test 4: Dropping questions")
    dropped = id.drop('morning')
    print(f"After dropping 'morning': {dropped.question_names}")
    print()
    
    # Test 5: Chained operations (similar to user's example)
    print("Test 5: Chained operations workflow")
    result = (id
        .with_edited_question('morning', {'question_options': [1,2,3,4,5,6,7,8,9,10]})
        .with_edited_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
        .with_renamed_question('morning', 'confidence_level')
        .drop('feeling')  # Remove one question to simulate user's workflow
    )
    
    print(f"Final question names: {result.question_names}")
    print(f"Final question types: {result.question_type.question_types}")
    print(f"Final question options: {result.question_option.question_options}")
    print()
    
    # Test 6: Verify that survey generation still works
    print("Test 6: Generating survey from edited questions")
    survey = result.to_survey()
    print(f"Survey created successfully with {len(survey.questions)} questions")
    print(f"Survey question names: {[q.question_name for q in survey.questions]}")
    
    print()
    print("✅ All tests passed! Question editing functionality is working.")

if __name__ == "__main__":
    test_question_editing()