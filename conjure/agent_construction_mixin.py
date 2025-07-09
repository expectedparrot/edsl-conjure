import random
import sys
from typing import Generator, List, Optional, Union, Callable
from edsl.agents import Agent
from edsl.agents import AgentList
from edsl.questions import QuestionBase
from edsl.results import Results
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn


class AgentConstructionMixin:
    def agent(self, index) -> Agent:
        """Return an agent constructed from the data.

        :param index: The index of the agent to construct.

        >>> from .input_data import InputDataABC
        >>> id = InputDataABC.example()
        >>> id.agent(0)
        Agent(traits = {'morning': '1', 'feeling': '3'}, codebook = {'morning': 'how are you doing this morning?', 'feeling': 'how are you feeling?'})


        """
        responses = [responses[index] for responses in self.raw_data]
        traits = {qn: r for qn, r in zip(self.question_names, responses)}

        a = Agent(traits=traits, codebook=self.names_to_texts)

        def construct_answer_dict_function(traits: dict) -> Callable:
            def func(self, question: "QuestionBase", scenario=None):
                return traits.get(question.question_name, None)

            return func

        a.add_direct_question_answering_method(construct_answer_dict_function(traits))
        return a

    def _agents(self, indices) -> Generator[Agent, None, None]:
        """Return a generator of agents, one for each index."""
        for idx in indices:
            yield self.agent(idx)

    def to_agent_list(
        self,
        indices: Optional[List] = None,
        sample_size: int = None,
        seed: str = "edsl",
        remove_direct_question_answering_method: bool = True,
    ) -> AgentList:
        """Return an AgentList from the data.

        :param indices: The indices of the agents to include.
        :param sample_size: The number of agents to sample.
        :param seed: The seed for the random number generator.

        >>> from .input_data import InputDataABC
        >>> id = InputDataABC.example()
        >>> al = id.to_agent_list()
        >>> len(al) == id.num_observations
        True
        >>> al = id.to_agent_list(indices = [0, 1, 2])
        Traceback (most recent call last):
        ...
        ValueError: Index 2 is greater than the number of agents 2.
        """
        if indices and (sample_size or seed != "edsl"):
            raise ValueError(
                "You cannot pass both indices and sample_size/seed, as these are mutually exclusive."
            )

        if indices:
            if len(indices) == 0:
                raise ValueError("Indices must be a non-empty list.")
            if max(indices) >= self.num_observations:
                raise ValueError(
                    f"Index {max(indices)} is greater than the number of agents {self.num_observations}."
                )
            if min(indices) < 0:
                raise ValueError(f"Index {min(indices)} is less than 0.")

        if indices is None:
            if sample_size is None:
                indices = range(self.num_observations)
            else:
                if sample_size > self.num_observations:
                    raise ValueError(
                        f"Sample size {sample_size} is greater than the number of agents {self.num_observations}."
                    )
                random.seed(seed)
                indices = random.sample(range(self.num_observations), sample_size)

        agents = list(self._agents(indices))
        if remove_direct_question_answering_method:
            for a in agents:
                a.remove_direct_question_answering_method()
        return AgentList(agents)

    def to_results(
        self,
        indices: Optional[List] = None,
        sample_size: int = None,
        seed: str = "edsl",
        dryrun=False,
        disable_remote_cache: bool = False,
        disable_remote_inference: bool = True,
        verbose: bool = False,
    ) -> Union[Results, None]:
        """Return the results of the survey.

        :param indices: The indices of the agents to include.
        :param sample_size: The number of agents to sample.
        :param seed: The seed for the random number generator.
        :param dryrun: If True, the survey will not be run, but the time to run it will be printed.
        :param verbose: If True, display detailed progress information to stderr.

        >>> from .input_data import InputDataABC
        >>> id = InputDataABC.example()
        >>> r = id.to_results(disable_remote_cache = True, disable_remote_inference = True)
        >>> len(r) == id.num_observations
        True
        """
        console = Console(stderr=True)
        
        if verbose:
            console.print("[bold blue]Starting survey conversion process...[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            disable=not verbose
        ) as progress:
            
            # Step 1: Create agent list
            agent_task = progress.add_task("[cyan]Creating agent list...", total=None)
            if verbose:
                console.print(f"[dim]Processing {self.num_observations} observations from {self.datafile_name}[/dim]")
            
            agent_list = self.to_agent_list(
                indices=indices,
                sample_size=sample_size,
                seed=seed,
                remove_direct_question_answering_method=False,
            )
            progress.update(agent_task, completed=1, total=1)
            
            # Step 2: Create survey
            survey_task = progress.add_task("[cyan]Creating survey...", total=None)
            if verbose:
                console.print(f"[dim]Processing {len(self.question_names)} questions[/dim]")
            
            survey = self.to_survey(verbose=verbose)
            progress.update(survey_task, completed=1, total=1)
            
            # Step 3: Handle dryrun
            if dryrun:
                import time
                
                dryrun_task = progress.add_task("[yellow]Running dryrun...", total=None)
                DRYRUN_SAMPLE = 30
                
                if verbose:
                    console.print(f"[dim]Running dryrun with {DRYRUN_SAMPLE} agents[/dim]")

                start = time.time()
                _ = survey.by(agent_list.sample(DRYRUN_SAMPLE)).run(
                    disable_remote_cache=disable_remote_cache,
                    disable_remote_inference=disable_remote_inference,
                )
                end = time.time()
                
                progress.update(dryrun_task, completed=1, total=1)
                
                console.print(f"[green]✓[/green] Time to run {DRYRUN_SAMPLE} agents: {round(end - start, 2)}s")
                time_per_agent = (end - start) / DRYRUN_SAMPLE
                full_sample_time = time_per_agent * len(agent_list)
                
                if full_sample_time < 60:
                    console.print(f"[dim]Full sample will take about {round(full_sample_time, 2)} seconds.[/dim]")
                elif full_sample_time < 3600:
                    console.print(f"[dim]Full sample will take about {round(full_sample_time / 60, 2)} minutes.[/dim]")
                else:
                    console.print(f"[dim]Full sample will take about {round(full_sample_time / 3600, 2)} hours.[/dim]")
                return None
            
            # Step 4: Run the actual survey
            run_task = progress.add_task("[green]Running survey...", total=None)
            
            # If we have more than 10 agents and verbose is enabled, do a timing estimate
            if len(agent_list) > 10 and verbose:
                import time
                
                console.print(f"[dim]Running timing sample with first 10 agents out of {len(agent_list)}[/dim]")
                
                # Time the first 10 agents
                start_time = time.time()
                sample_results = survey.by(agent_list[:10]).run(
                    disable_remote_cache=disable_remote_cache,
                    disable_remote_inference=disable_remote_inference,
                )
                end_time = time.time()
                
                # Calculate timing estimates
                sample_time = end_time - start_time
                time_per_agent = sample_time / 10
                estimated_total_time = time_per_agent * len(agent_list)
                
                console.print(f"[green]✓[/green] Sample of 10 agents completed in {sample_time:.2f}s")
                console.print(f"[dim]Time per agent: {time_per_agent:.2f}s[/dim]")
                
                if estimated_total_time < 60:
                    console.print(f"[yellow]Estimated time for all {len(agent_list)} agents: {estimated_total_time:.1f} seconds[/yellow]")
                elif estimated_total_time < 3600:
                    console.print(f"[yellow]Estimated time for all {len(agent_list)} agents: {estimated_total_time / 60:.1f} minutes[/yellow]")
                else:
                    console.print(f"[yellow]Estimated time for all {len(agent_list)} agents: {estimated_total_time / 3600:.1f} hours[/yellow]")
                
                # Calculate estimated time for remaining agents
                remaining_agents = len(agent_list) - 10
                estimated_remaining_time = time_per_agent * remaining_agents
                
                if estimated_remaining_time < 60:
                    time_display = f"{estimated_remaining_time:.1f} seconds"
                elif estimated_remaining_time < 3600:
                    time_display = f"{estimated_remaining_time / 60:.1f} minutes"
                else:
                    time_display = f"{estimated_remaining_time / 3600:.1f} hours"
                
                console.print(f"[dim]Now running full survey with remaining {remaining_agents} agents (estimated time: {time_display})[/dim]")
                
                # Start full survey timer
                full_survey_start = time.time()
                
                # Run the remaining agents
                remaining_results = survey.by(agent_list[10:]).run(
                    disable_remote_cache=disable_remote_cache,
                    disable_remote_inference=disable_remote_inference,
                )
                
                # Calculate total elapsed time
                total_elapsed = time.time() - full_survey_start + sample_time
                if total_elapsed < 60:
                    console.print(f"[green]✓[/green] Total elapsed time: {total_elapsed:.1f} seconds")
                elif total_elapsed < 3600:
                    console.print(f"[green]✓[/green] Total elapsed time: {total_elapsed / 60:.1f} minutes")
                else:
                    console.print(f"[green]✓[/green] Total elapsed time: {total_elapsed / 3600:.1f} hours")
                
                # Combine results
                results = sample_results + remaining_results
                
            else:
                if verbose:
                    console.print(f"[dim]Running survey with {len(agent_list)} agents[/dim]")
                
                # Start timer for full survey
                import time
                survey_start = time.time()
                
                results = survey.by(agent_list).run(
                    disable_remote_cache=disable_remote_cache,
                    disable_remote_inference=disable_remote_inference,
                )
                
                # Calculate elapsed time
                elapsed = time.time() - survey_start
                if verbose:
                    if elapsed < 60:
                        console.print(f"[green]✓[/green] Total elapsed time: {elapsed:.1f} seconds")
                    elif elapsed < 3600:
                        console.print(f"[green]✓[/green] Total elapsed time: {elapsed / 60:.1f} minutes")
                    else:
                        console.print(f"[green]✓[/green] Total elapsed time: {elapsed / 3600:.1f} hours")
            
            progress.update(run_task, completed=1, total=1)
            
            if verbose:
                console.print("[bold green]✓ Survey conversion completed successfully![/bold green]")
            
            return results


if __name__ == "__main__":
    import doctest

    doctest.testmod(optionflags=doctest.ELLIPSIS)
