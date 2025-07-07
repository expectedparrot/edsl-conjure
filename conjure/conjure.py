from typing import List, Optional, Dict, Callable


class Conjure:
    def __new__(cls, datafile_name: str, *args, **kwargs):

        from .input_data_csv import InputDataCSV
        from .input_data_spss import InputDataSPSS
        from .input_data_stata import InputDataStata

        handlers = {
            "csv": InputDataCSV,
            "sav": InputDataSPSS,
            "dta": InputDataStata,
        }

        handler = handlers.get(datafile_name.split(".")[-1])
        if handler is None:
            raise ValueError("Unsupported file type")
        
        return handler(datafile_name, *args, **kwargs)

    def __init__(
        self,
        datafile_name: str,
        config: Optional[dict] = None,
        naming_function: Optional[Callable] = None,
        raw_data: Optional[List] = None,
        question_names: Optional[List[str]] = None,
        question_texts: Optional[List[str]] = None,
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


    