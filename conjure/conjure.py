from typing import List, Optional, Dict, Callable, Union
from edsl import FileStore

class Conjure:
    def __new__(cls, datafile_name: Union[str, FileStore], *args, **kwargs):

        from .input_data_csv import InputDataCSV
        from .input_data_spss import InputDataSPSS
        from .input_data_stata import InputDataStata

        if isinstance(datafile_name, FileStore):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_with_extension = temp_file.name + "." + datafile_name.suffix
                datafile_name.write(temp_file_with_extension)
                datafile_name = temp_file_with_extension

        handlers = {
            "csv": InputDataCSV,
            "sav": InputDataSPSS,
            "dta": InputDataStata,
        }

        file_type = datafile_name.split(".")[-1]

        handler = handlers.get(file_type)
        if handler is None:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        instance = handler(datafile_name, *args, **kwargs)
        return instance

    def __init__(
        self,
        datafile_name: str,
        config: Optional[dict] = None,
        naming_function: Optional[Callable] = None,
        raw_data: Optional[List] = None,
        question_names: Optional[List[str]] = None,
        question_texts: Optional[List[str]] = None,
        question_names_to_question_text: Optional[Dict[str, str]] = None,
        answer_codebook: Optional[Dict] = None,
        question_types: Optional[List[str]] = None,
        question_options: Optional[List] = None,
        order_options=False,
        question_name_repair_func: Callable = None,
    ):
        # The __init__ method in Conjure won't be called because __new__ returns a different class instance.
        pass

    @classmethod
    def example(cls):
        from InputData import InputDataABC

        return InputDataABC.example()


    