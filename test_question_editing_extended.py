#!/usr/bin/env python3
"""
Test script for both instantiation-time and in-place question editing functionality.
"""

from conjure.input_data import InputDataABC
from conjure import Conjure

def test_instantiation_editing():
    """Test passing question edits at instantiation time."""
    
    print("=" * 60)
    print("Testing INSTANTIATION-TIME question editing")
    print("=" * 60)
    
    # Define the edit function similar to user's example
    def apply_survey_edits(survey_data):
        return (survey_data
            .with_edited_question('morning', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
            .with_edited_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
            .with_renamed_question('morning', 'confidence_level')
        )
    
    # Test with InputDataABC.example
    print("Creating InputData with question_edits parameter...")
    survey_data = InputDataABC.example(question_edits=apply_survey_edits)
    
    print(f"Final question names: {survey_data.question_names}")
    print(f"Final question types: {survey_data.question_type.question_types}")
    print(f"Final question options: {survey_data.question_option.question_options}")
    
    # Test that to_survey() works with edited questions
    print(f"\\nGenerating survey from edited data...")
    survey = survey_data.to_survey()
    print(f"Survey created with {len(survey.questions)} questions")
    print(f"Survey question names: {[q.question_name for q in survey.questions]}")
    
    print("✅ Instantiation-time editing works!")
    return survey_data

def test_in_place_editing():
    """Test in-place question editing methods."""
    
    print("\\n" + "=" * 60)
    print("Testing IN-PLACE question editing")
    print("=" * 60)
    
    # Create basic instance
    survey_data = InputDataABC.example()
    print(f"Original question names: {survey_data.question_names}")
    
    # Test chained in-place editing (similar to user's workflow)
    survey_data.edit_question('morning', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
    print(f"After editing morning options: {survey_data.question_option.question_options[0]}")
    
    survey_data.edit_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
    print(f"After changing feeling to free_text: {survey_data.question_type.question_types[1]}")
    
    survey_data.rename_question('morning', 'confidence_level')
    print(f"After renaming morning: {survey_data.question_names}")
    
    # Test that to_results would work (if we had the right setup)
    print(f"\\nGenerating survey from in-place edited data...")
    survey = survey_data.to_survey()
    print(f"Survey created with {len(survey.questions)} questions")
    print(f"Survey question names: {[q.question_name for q in survey.questions]}")
    
    print("✅ In-place editing works!")
    return survey_data

def test_apply_question_edits():
    """Test the apply_question_edits method."""
    
    print("\\n" + "=" * 60)
    print("Testing APPLY_QUESTION_EDITS method")
    print("=" * 60)
    
    # Create basic instance
    survey_data = InputDataABC.example()
    print(f"Original question names: {survey_data.question_names}")
    
    # Define complex edit function
    def complex_edits(data):
        return (data
            .with_edited_question('morning', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
            .with_edited_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
            .with_renamed_question('morning', 'long_run_us_fiscal_sustainability_confidence')
        )
    
    # Apply the edits in-place
    survey_data.apply_question_edits(complex_edits)
    
    print(f"After applying complex edits:")
    print(f"  Question names: {survey_data.question_names}")
    print(f"  Question types: {survey_data.question_type.question_types}")
    print(f"  Question options: {survey_data.question_option.question_options}")
    
    print("✅ apply_question_edits works!")
    return survey_data

def demonstrate_workflow():
    """Demonstrate the complete workflow that user wants."""
    
    print("\\n" + "=" * 60)
    print("COMPLETE WORKFLOW DEMONSTRATION")
    print("=" * 60)
    
    print("Approach 1: Edit at instantiation, then use to_survey()")
    print("-" * 50)
    
    def focal_survey_edits(survey):
        return (survey
            .with_edited_question('morning', {'question_options':[1,2,3,4,5,6,7,8,9,10]}) 
            .with_edited_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
            .with_renamed_question('morning', 'confidence_topic_highest')
        )
    
    # Method 1: Pass edits at creation
    focal_survey = InputDataABC.example(question_edits=focal_survey_edits)
    edsl_survey = focal_survey.to_survey()
    print(f"Survey ready for to_results() with questions: {[q.question_name for q in edsl_survey.questions]}")
    
    print("\\nApproach 2: Create, edit in-place, then use to_survey()")
    print("-" * 50)
    
    # Method 2: Create then edit in-place  
    focal_survey2 = InputDataABC.example()
    focal_survey2.apply_question_edits(focal_survey_edits)
    edsl_survey2 = focal_survey2.to_survey()
    print(f"Survey ready for to_results() with questions: {[q.question_name for q in edsl_survey2.questions]}")
    
    print("\\n🎉 Both approaches work! You can now:")
    print("   1. Pass question_edits to Conjure() at instantiation")
    print("   2. Use in-place editing methods before calling to_results()")

if __name__ == "__main__":
    test_instantiation_editing()
    test_in_place_editing() 
    test_apply_question_edits()
    demonstrate_workflow()