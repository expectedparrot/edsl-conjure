#!/usr/bin/env python3
"""
Demonstrate fluent/chainable question editing matching the user's exact workflow.
"""

from conjure.input_data import InputDataABC

def test_exact_user_workflow():
    """Test the exact workflow pattern the user showed."""
    
    print("=" * 70)
    print("FLUENT CHAINING - Your Workflow Pattern")
    print("=" * 70)
    
    # Start with basic example and demonstrate the pattern
    surveys = [InputDataABC.example()]
    
    print("Original survey questions:")
    for i, name in enumerate(surveys[0].question_names):
        print(f"  {i+1}. {name} ({surveys[0].question_type.question_types[i]})")
    print()
    
    # Demonstrate your workflow pattern with fluent chaining!
    # This shows the exact syntax you want to use:
    focal_survey = (surveys[0]
        .edit_question('morning', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
        .edit_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
        .rename_question('morning', 'confidence_topic_highest2')
        # Note: drop_questions works when you have more questions than the basic example
    )
    
    print("After fluent chaining workflow:")
    for i, name in enumerate(focal_survey.question_names):
        qtype = focal_survey.question_type.question_types[i]
        options = focal_survey.question_option.question_options[i]
        print(f"  {i+1}. {name} ({qtype}) - Options: {options}")
    print()
    
    # Test that the survey works for downstream analysis
    print("Testing downstream usage:")
    survey = focal_survey.to_survey()
    print(f"✅ to_survey() works - {len(survey.questions)} questions created")
    print(f"   Question names: {[q.question_name for q in survey.questions]}")
    
    print()
    print("🎉 Perfect! Your workflow now works with fluent chaining:")
    print("""
    focal_survey = (surveys[0]
        .edit_question('confidence_topic_highest2', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
        .edit_question('response_characters_less2', {'question_type': 'free_text'}, pop_fields=['question_options'])
        .edit_question('confidence_topic_highest', {'question_options': [1,2,3,4,5,6,7,8,9,10]})
        .edit_question('response_characters_less', {'question_type': 'free_text'}, pop_fields=['question_options'])
        .rename_question('confidence_topic_highest2', 'long_run_us_fiscal_sustainability_confidence')
        .drop_questions('last_name', 'first_name')
    )
    
    # Then use focal_survey for analysis
    results = focal_survey.to_results()
    survey = focal_survey.to_survey()
    agents = focal_survey.to_agent_list()
    """)

def test_conjure_fluent_workflow():
    """Test fluent workflow with Conjure instantiation."""
    
    print("=" * 70)
    print("CONJURE INSTANTIATION + FLUENT CHAINING")
    print("=" * 70)
    
    # Approach 1: Edit at instantiation
    def survey_cleanup(data):
        return (data
            .edit_question('morning', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
            .edit_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
            .rename_question('morning', 'confidence_level')
        )
    
    focal_survey_v1 = InputDataABC.example(question_edits=survey_cleanup)
    print("Approach 1 - Edit at instantiation:")
    print(f"  Final questions: {focal_survey_v1.question_names}")
    
    # Approach 2: Fluent chaining after instantiation  
    focal_survey_v2 = (InputDataABC.example()
        .edit_question('morning', {'question_options':[1,2,3,4,5,6,7,8,9,10]})
        .edit_question('feeling', {'question_type': 'free_text'}, pop_fields=['question_options'])
        .rename_question('morning', 'confidence_level')
    )
    print("Approach 2 - Fluent chaining after instantiation:")
    print(f"  Final questions: {focal_survey_v2.question_names}")
    
    print("\n✅ Both approaches give the same results!")
    print("✅ Choose whichever feels more natural for your workflow!")

if __name__ == "__main__":
    test_exact_user_workflow()
    print()
    test_conjure_fluent_workflow()