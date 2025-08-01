import base64
import sys
from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional, List, Generator, Tuple, Union
from collections import namedtuple
from typing import List, Union

from edsl.questions import QuestionBase
from edsl.scenarios import ScenarioList
from edsl.surveys import Survey
from edsl.utilities import is_valid_variable_name
from edsl.dataset import Dataset
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


from .survey_responses import SurveyResponses
from .naming_utilities import sanitize_string
from .raw_question import RawQuestion
from .agent_construction_mixin import AgentConstructionModule
from .question_option_mixin import QuestionOptionModule
from .input_data_mixin_question_stats import QuestionStatsModule
from .question_type_mixin import QuestionTypeModule
from .question_error_logger import QuestionErrorLogger, set_global_logger, log_creation_error


class InputDataABC(ABC):
    """A class to represent the input data for a survey."""

    NUM_UNIQUE_THRESHOLD = 15
    FRAC_NUMERICAL_THRESHOLD = 0.8
    MULTIPLE_CHOICE_OTHER_THRESHOLD = 0.5
    OTHER_STRING = "Other:"

    question_attributes = [
        "num_responses",
        "num_unique_responses",
        "missing",
        "unique_responses",
        "frac_numerical",
        "top_5",
        "frac_obs_from_top_5",
    ]
    QuestionStats = namedtuple("QuestionStats", question_attributes)

    def __init__(
        self,
        datafile_name: str,
        config: Optional[dict] = None,
        naming_function: Optional[Callable] = sanitize_string,
        raw_data: Optional[List] = None,
        binary: Optional[str] = None,
        question_names: Optional[List[str]] = None,
        question_texts: Optional[List[str]] = None,
        question_names_to_question_text: Optional[Dict[str, str]] = None,
        answer_codebook: Optional[Dict] = None,
        question_types: Optional[List[str]] = None,
        question_options: Optional[List] = None,
        order_options=False,
        question_name_repair_func: Callable = None,
    ):
        """Initialize the InputData object.

        :param datafile_name: The name of the file containing the data.
        :param config: The configuration parameters for reading the data.
        :param raw_data: The raw data in the form of a dictionary.
        :param question_names: The names of the questions.
        :param question_texts: The text of the questions.
        :param answer_codebook: The codebook for the answers.
        :param question_types: The types of the questions.
        :param question_options: The options for the questions.

        >>> id = InputDataABC.example(question_names = ['a','b'], answer_codebook = {'a': {'1':'yes', '2':'no'}, 'b': {'1':'yes', '2':'no'}})

        >>> id = InputDataABC.example(question_names = ['a','b'], answer_codebook = {'a': {'1':'yes', '2':'no'}, 'c': {'1':'yes', '2':'no'}})
        Traceback (most recent call last):
        ...
        Exception: The keys of the answer_codebook must match the question_names.
        """

        self.datafile_name = datafile_name
        self.config = config
        self.naming_function = naming_function

        if binary is not None:
            self.binary = binary
        else:
            try:
                with open(self.datafile_name, "rb") as file:
                    self.binary = base64.b64encode(file.read()).decode()
            except FileNotFoundError:
                self.binary = None

        def default_repair_func(x):
            return (
                x.replace("#", "_num")
                .replace("class", "social_class")
                .replace("name", "respondent_name")
            )

        self.question_name_repair_func = (
            question_name_repair_func or default_repair_func
        )

        if answer_codebook is not None and question_names is not None:
            if set(answer_codebook.keys()) != set(question_names):
                raise Exception(
                    "The keys of the answer_codebook must match the question_names."
                )

        if question_names is not None and question_texts is not None:
            if len(question_names) != len(question_texts):
                raise Exception(
                    "The question_names and question_texts must have the same length."
                )

        self.question_texts = question_texts
        self.question_names = question_names
        self.question_names_to_question_text = question_names_to_question_text
        self.answer_codebook = answer_codebook
        self.raw_data = raw_data

        self.apply_codebook()

        # Initialize modules using composition instead of mixins
        self.question_stats = QuestionStatsModule(self)
        self.question_type = QuestionTypeModule(self)
        self.question_option = QuestionOptionModule(self)
        self.agent_construction = AgentConstructionModule(self)

        self.question_type.question_types = question_types
        self.question_option.question_options = question_options
        if order_options:
            self.question_option.order_options()
            
        # Store verbose flag for use in methods
        self._verbose = False
        
        # Initialize question error logger
        self.question_error_logger = QuestionErrorLogger(datafile_name, verbose=False)
        set_global_logger(self.question_error_logger)

    # Properties for backward compatibility with mixin interface
    @property
    def question_types(self):
        return self.question_type.question_types
    
    @question_types.setter
    def question_types(self, value):
        self.question_type.question_types = value
    
    @property
    def question_options(self):
        return self.question_option.question_options
    
    @question_options.setter
    def question_options(self, value):
        self.question_option.question_options = value
    
    # Question stats methods
    def question_statistics(self, question_name: str):
        return self.question_stats.question_statistics(question_name)
    
    @property
    def num_responses(self):
        return self.question_stats.num_responses
    
    @property
    def num_unique_responses(self):
        return self.question_stats.num_unique_responses
    
    @property
    def missing(self):
        return self.question_stats.missing
    
    @property
    def frac_numerical(self):
        return self.question_stats.frac_numerical
    
    @property
    def frac_obs_from_top_5(self):
        return self.question_stats.frac_obs_from_top_5
    
    @property
    def top_5(self):
        return self.question_stats.top_5
    
    @property
    def unique_responses(self):
        return self.question_stats.unique_responses
    
    def unique_responses_more_than_k(self, k, remove_missing=True):
        return self.question_stats.unique_responses_more_than_k(k, remove_missing)
    
    def top_k(self, k):
        return self.question_stats.top_k(k)
    
    def frac_obs_from_top_k(self, k):
        return self.question_stats.frac_obs_from_top_k(k)
    
    # Agent construction methods
    def agent(self, index):
        return self.agent_construction.agent(index)
    
    def to_agent_list(self, indices=None, sample_size=None, seed="edsl", remove_direct_question_answering_method=True):
        return self.agent_construction.to_agent_list(indices, sample_size, seed, remove_direct_question_answering_method)
    
    def to_results(self, indices=None, sample_size=None, seed="edsl", dryrun=False, disable_remote_cache=False, disable_remote_inference=True, verbose=False):
        return self.agent_construction.to_results(indices, sample_size, seed, dryrun, disable_remote_cache, disable_remote_inference, verbose)
    
    def order_options(self):
        return self.question_option.order_options()

    @property
    def download_link(self):
        from IPython.display import HTML

        actual_file_name = self.datafile_name.split("/")[-1]
        download_link = f'<a href="data:text/plain;base64,{self.binary}" download="{actual_file_name}">Download {self.datafile_name}</a>'
        return HTML(download_link)

    @abstractmethod
    def get_question_texts(self) -> List[str]:
        """Get the text of the questions

        >>> id = InputDataABC.example()
        >>> id.get_question_texts()
        ['how are you doing this morning?', 'how are you feeling?']

        """
        raise NotImplementedError

    @abstractmethod
    def get_raw_data(self) -> List[List[str]]:
        """Returns the responses by reading the datafile_name.

        >>> id = InputDataABC.example()
        >>> id.get_raw_data()
        [['1', '4'], ['3', '6']]

        """
        raise NotImplementedError

    @abstractmethod
    def get_question_names(self) -> List[str]:
        """Get the names of the questions.

        >>> id = InputDataABC.example()
        >>> id.get_question_names()
        ['morning', 'feeling']

        """
        raise NotImplementedError

    def rename_questions(
        self, rename_dict: Dict[str, str], ignore_missing=False
    ) -> "InputData":
        """Rename a question.

        >>> id = InputDataABC.example()
        >>> id.rename_questions({'morning': 'evening'}).question_names
        ['evening', 'feeling']

        """
        for old_name, new_name in rename_dict.items():
            self.rename(old_name, new_name, ignore_missing=ignore_missing)
        return self

    def rename(self, old_name, new_name, ignore_missing=False) -> "InputData":
        """Rename a question.

        >>> id = InputDataABC.example()
        >>> id.rename('morning', 'evening').question_names
        ['evening', 'feeling']

        """
        if old_name not in self.question_names:
            if ignore_missing:
                return self
            else:
                raise ValueError(f"Question {old_name} not found.")

        idx = self.question_names.index(old_name)
        self.question_names[idx] = new_name
        self.answer_codebook[new_name] = self.answer_codebook.pop(old_name, {})

        return self

    def _drop_question(self, question_name, ignore_missing=False):
        """Drop a question

        >>> id = InputDataABC.example()
        >>> id._drop_question('morning').question_names
        ['feeling']

        """
        if question_name not in self.question_names:
            if ignore_missing:
                return self
            else:
                raise ValueError(f"Question {question_name} not found.")
        idx = self.question_names.index(question_name)
        self._question_names.pop(idx)
        self._question_texts.pop(idx)
        self.question_type.question_types.pop(idx)
        self.question_option.question_options.pop(idx)
        self.raw_data.pop(idx)
        self.answer_codebook.pop(question_name, None)
        return self

    def drop(self, *question_names_to_drop) -> "InputData":
        """Drop a question.

        >>> id = InputDataABC.example()
        >>> id.drop('morning').question_names
        ['feeling']

        """
        for qn in question_names_to_drop:
            self._drop_question(qn)
        return self

    def keep(self, *question_names_to_keep, ignore_missing=False) -> "InputDataABC":
        """Keep a question.

        >>> id = InputDataABC.example()
        >>> id.keep('morning').question_names
        ['morning']

        """
        all_question_names = self._question_names[:]
        for qn in all_question_names:
            if qn not in question_names_to_keep:
                self._drop_question(qn, ignore_missing=ignore_missing)
        return self

    def modify_question_type(
        self,
        question_name: str,
        new_type: str,
        drop_options: bool = False,
        new_options: Optional[List[str]] = None,
    ) -> "InputData":
        """Modify the question type of a question. Checks to make sure the new type is valid.

        >>> id = InputDataABC.example()
        >>> id.modify_question_type('morning', 'numerical', drop_options = True).question_types
        ['numerical', 'multiple_choice']

        >>> id = InputDataABC.example()
        >>> id.modify_question_type('morning', 'poop')
        Traceback (most recent call last):
        ...
        ValueError: Question type poop is not available.
        """
        old_type = self.question_type.question_types[self.question_names.index(question_name)]
        old_options = self.question_option.question_options[self.question_names.index(question_name)]

        from edsl.questions import Question

        if new_type not in Question.available():
            raise ValueError(f"Question type {new_type} is not available.")

        idx = self.question_names.index(question_name)
        self.question_type.question_types[idx] = new_type
        if drop_options:
            self.question_option.question_options[idx] = None
        if new_options is not None:
            self.question_option.question_options[idx] = new_options

        try:
            idx = self.question_names.index(question_name)
            rq = self.raw_question(idx)
            q = rq.to_question()
        except Exception as e:
            # Log error to centralized logger instead of printing to stderr
            options_info = getattr(rq, 'options', 'N/A') if 'rq' in locals() else 'N/A'
            self.question_error_logger.log_question_error(
                question_name=question_name,
                error_type="Question Type Modification Failed",
                details=f"Failed to modify question type to '{new_type}'. Too few question options (got {options_info}). Reverting changes.",
                exception=e
            )
            self.question_type.question_types[idx] = old_type
            self.question_option.question_options[idx] = old_options
        return self

    @property
    def num_observations(self):
        """Return the number of observations.

        >>> id = InputDataABC.example()
        >>> id.num_observations
        2

        """
        return len(self.raw_data[0])

    def to_dict(self):
        return {
            "datafile_name": self.datafile_name,
            "config": self.config,
            "raw_data": self.raw_data,
            "question_names": self.question_names,
            "question_texts": self.question_texts,
            "binary": self.binary,
            "answer_codebook": self.answer_codebook,
            "question_types": self.question_type.question_types,
        }

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(**d)

    @property
    def question_names(self) -> List[str]:
        """
        Return a list of question names.

        >>> id = InputDataABC.example()
        >>> id.question_names
        ['morning', 'feeling']

        We can pass question names instead:

        >>> id = InputDataABC.example(question_names = ['a','b'])
        >>> id.question_names
        ['a', 'b']

        """
        if not hasattr(self, "_question_names"):
            self.question_names = None
        return self._question_names

    @question_names.setter
    def question_names(self, value) -> None:
        if value is None:
            value = self.get_question_names()
            if len(set(value)) != len(value):
                raise ValueError("Question names must be unique.")
            for i, qn in enumerate(value):
                if not is_valid_variable_name(qn, allow_name=False):
                    new_name = self.question_name_repair_func(qn)
                    if not is_valid_variable_name(new_name, allow_name=False):
                        raise ValueError(
                            f"""Question names must be valid Python identifiers. '{qn}' is not.""",
                            """You can pass an entry in question_name_repair_func to fix this.""",
                        )
                    else:
                        value[i] = new_name
                else:
                    value[i] = qn
        self._question_names = value

    @property
    def question_texts(self) -> List[str]:
        """
        Return a list of question texts.

        >>> id = InputDataABC.example()
        >>> id.question_texts
        ['how are you doing this morning?', 'how are you feeling?']
        """
        if not hasattr(self, "_question_texts"):
            self.question_texts = None
        return self._question_texts

    @question_texts.setter
    def question_texts(self, value):
        if value is None:
            value = self.get_question_texts()
        self._question_texts = value

    @property
    def raw_data(self):
        """

        >>> id = InputDataABC.example()
        >>> id.raw_data
        [['1', '4'], ['3', '6']]

        """
        if not hasattr(self, "_raw_data"):
            self.raw_data = None
        return self._raw_data

    @raw_data.setter
    def raw_data(self, value):
        """ """
        if value is None:
            value = self.get_raw_data()
            # self.apply_codebook()
        self._raw_data = value

    def to_dataset(self) -> "Dataset":
        dataset_list = []
        for key, value in zip(self.question_names, self.raw_data):
            dataset_list.append({key: value})
        return Dataset(dataset_list)

    def to_scenario_list(self) -> ScenarioList:
        """Return a ScenarioList object from the raw response data.

        >>> id = InputDataABC.example()
        >>> s = id.to_scenario_list()
        >>> type(s) == ScenarioList
        True

        >>> s
        ScenarioList([Scenario({'morning': '1', 'feeling': '3'}), Scenario({'morning': '4', 'feeling': '6'})])

        """
        s = ScenarioList()
        for qn in self.question_names:
            idx = self.question_names.index(qn)
            s = s.add_list(qn, self.raw_data[idx])
        return s

    @property
    def names_to_texts(self) -> dict:
        """
        Return a dictionary of question names to question texts.

        >>> id = InputDataABC.example()
        >>> id.names_to_texts
        {'morning': 'how are you doing this morning?', 'feeling': 'how are you feeling?'}
        """
        return {n: t for n, t in zip(self.question_names, self.question_texts)}

    @property
    def texts_to_names(self):
        """Return a dictionary of question texts to question names.

        >>> id = InputDataABC.example()
        >>> id.texts_to_names
        {'how are you doing this morning?': 'morning', 'how are you feeling?': 'feeling'}

        """
        return {t: n for n, t in self.names_to_texts.items()}

    def raw_question(self, index: int) -> RawQuestion:
        question_name = self.question_names[index]
        
        # Use question_names_to_question_text mapping if available, otherwise use question_texts
        # Use case-insensitive matching for dictionary lookups
        if self.question_names_to_question_text and question_name.lower() in self.question_names_to_question_text:
            question_text = self.question_names_to_question_text[question_name.lower()]
        else:
            question_text = self.question_texts[index]
        
        return RawQuestion(
            question_type=self.question_type.question_types[index],
            question_name=question_name,
            question_text=question_text,
            responses=self.raw_data[index],
            question_options=self.question_option.question_options[index],
        )

    def raw_questions(self) -> Generator[RawQuestion, None, None]:
        """Return a generator of RawQuestion objects."""
        for qn in self.question_names:
            idx = self.question_names.index(qn)
            yield self.raw_question(idx)

    def questions(self) -> Generator[Union[QuestionBase, None], None, None]:
        """Return a generator of Question objects."""
        for rq in self.raw_questions():
            try:
                yield rq.to_question()
            except Exception as e:
                # Log error to centralized logger instead of printing to stderr
                options_info = getattr(rq, 'options', 'N/A')
                log_creation_error(rq.question_name, e)
                yield None

    def select(self, *question_names: List[str]) -> "InputData":
        """Select a subset of the questions.

        :param question_names: The names of the questions to select.

        >>> id = InputDataABC.example()
        >>> id.select('morning').question_names
        ['morning']

        """

        idxs = [self.question_names.index(qn) for qn in question_names]
        new_data = [self.raw_data[i] for i in idxs]
        new_texts = [self.question_texts[i] for i in idxs]
        new_types = [self.question_type.question_types[i] for i in idxs]
        new_options = [self.question_option.question_options[i] for i in idxs]
        new_names = [self.question_names[i] for i in idxs]
        answer_codebook = {
            qn: self.answer_codebook.get(qn, {}) for qn in question_names
        }
        return self.__class__(
            self.datafile_name,
            self.config,
            raw_data=new_data,
            question_names=new_names,
            question_texts=new_texts,
            question_types=new_types,
            question_options=new_options,
            answer_codebook=answer_codebook,
            question_name_repair_func=self.question_name_repair_func,
        )

    def to_survey(self, verbose: bool = False, progress_callback=None) -> Survey:
        """
        >>> id = InputDataABC.example()
        >>> s = id.to_survey()
        >>> type(s) == Survey
        True

        """
        console = Console(stderr=True)
        s = Survey()
        
        questions_list = list(self.questions())
        
        if verbose:
            console.print(f"[dim]Building survey from {len(questions_list)} questions[/dim]")
        
        # If we have a progress callback, use it instead of creating our own progress
        if progress_callback:
            for i, q in enumerate(questions_list):
                if q is not None:
                    s.add_question(q)
                if i % max(1, len(questions_list) // 20) == 0:  # Update every 5%
                    progress_callback(i + 1)
        else:
            # Use our own progress bar when no callback provided
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                disable=not verbose
            ) as progress:
                
                task = progress.add_task("[cyan]Adding questions to survey...", total=len(questions_list))
                
                for i, q in enumerate(questions_list):
                    if q is not None:
                        s.add_question(q)
                    if i % max(1, len(questions_list) // 10) == 0:  # Update every 10%
                        progress.update(task, completed=i + 1)
                        
                progress.update(task, completed=len(questions_list))
            
        if verbose:
            valid_questions = sum(1 for q in questions_list if q is not None)
            invalid_questions = len(questions_list) - valid_questions
            console.print(f"[green]✓[/green] Added {valid_questions} valid questions to survey")
            if invalid_questions > 0:
                console.print(f"[yellow]⚠[/yellow] Skipped {invalid_questions} invalid questions")
        
        # Display error summary if there were any question processing errors
        if self.question_error_logger.has_errors():
            self.question_error_logger.display_summary()
            
        return s

    def print(self):
        sl = (
            ScenarioList.from_list("question_name", self.question_names)
            .add_list("question_text", self.question_texts)
            .add_list("inferred_question_type", self.question_type.question_types)
            .add_list("num_responses", self.num_responses)
            .add_list("num_unique_responses", self.num_unique_responses)
            .add_list("missing", self.missing)
            .add_list("frac_numerical", self.frac_numerical)
            .add_list("top_5_items", self.question_stats.top_k(5))
            .add_list("frac_obs_from_top_5", self.question_stats.frac_obs_from_top_k(5))
        )
        sl.print()

    @property
    def answer_codebook(self) -> dict:
        """Return the answer codebook.
        >>> id = InputDataABC.example(answer_codebook = {'morning':{'1':'hello'}})
        >>> id.answer_codebook
        {'morning': {'1': 'hello'}}

        """
        if not hasattr(self, "_answer_codebook"):
            self._answer_codebook = None
        return self._answer_codebook

    @answer_codebook.setter
    def answer_codebook(self, value):
        if value is None:
            value = self.get_answer_codebook()
        self._answer_codebook = value

    def get_answer_codebook(self):
        return {}

    def _drop_rows(self, indices: List[int]):
        """Drop rows from the raw data.
        :param indices

        >>> id = InputDataABC.example()
        >>> id.num_observations
        2
        >>> _ = id._drop_rows([1])
        >>> id.num_observations
        1

        """
        self.raw_data = [
            [r for i, r in enumerate(row) if i not in indices] for row in self.raw_data
        ]
        return self

    def _missing_indices(self, question_name):
        """Return the indices of missing values for a question.
        TODO: Could re-factor to use SimpleEval

        >>> id = InputDataABC.example()
        >>> id.raw_data[0][0] = 'missing'
        >>> id._missing_indices('morning')
        [0]
        """
        idx = self.question_names.index(question_name)
        return [i for i, r in enumerate(self.raw_data[idx]) if r == "missing"]

    def drop_missing(self, question_name):
        """Drop missing values for a question.

        >>> id = InputDataABC.example()
        >>> id.num_observations
        2
        >>> id.raw_data[0][0] = 'missing'
        >>> id.drop_missing('morning')
        >>> id.num_observations
        1
        """
        self._drop_rows(self._missing_indices(question_name))

    @property
    def num_observations(self):
        """
        Return the number of observations

        >>> id = InputDataABC.example()
        >>> id.num_observations
        2
        """
        return len(self.raw_data[0])

    def apply_codebook(self) -> None:
        """Apply the codebook to the raw data.

        >>> id = InputDataABC.example()
        >>> id.raw_data
        [['1', '4'], ['3', '6']]

        >>> id = InputDataABC.example(answer_codebook = {'morning':{'1':'hello'}})
        >>> id.raw_data
        [['hello', '4'], ['3', '6']]
        """
        for index, qn in enumerate(self.question_names):
            if qn in self.answer_codebook:
                new_responses = [
                    self.answer_codebook[qn].get(r, r) for r in self.raw_data[index]
                ]
                self.raw_data[index] = new_responses

    def __repr__(self):
        return f"{self.__class__.__name__}: datafile_name:'{self.datafile_name}' num_questions:{len(self.question_names)}, num_observations:{len(self.raw_data[0])}"

    @classmethod
    def example(cls, **kwargs) -> "InputDataABC":
        class InputDataExample(InputDataABC):
            def get_question_texts(self) -> List[str]:
                """Get the text of the questions"""
                return ["how are you doing this morning?", "how are you feeling?"]

            def get_raw_data(self) -> SurveyResponses:
                """Returns a dataframe of responses by reading the datafile_name."""
                return [["1", "4"], ["3", "6"]]

            def get_question_names(self):
                new_names = [self.naming_function(q) for q in self.question_texts]
                if len(new_names) != len(set(new_names)):
                    new_names = [f"{q}_{i}" for i, q in enumerate(new_names)]
                return new_names

        return InputDataExample("notneeded", config={}, **kwargs)


if __name__ == "__main__":
    import doctest

    doctest.testmod(optionflags=doctest.ELLIPSIS)
