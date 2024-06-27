"""
    Local python interpreter to run the code, copy from vision agent Andrew Ng
"""
import nbformat
import time
import copy
import re
import traceback
import abc

from typing import IO, Any, Dict, Iterable, List, Optional, Union, cast
from enum import Enum
from pathlib import Path
from typing_extensions import Self
from pydantic import BaseModel, field_serializer


from nbclient import NotebookClient
from nbclient import __version__ as nbclient_version
from nbclient.exceptions import CellTimeoutError, DeadKernelError
from nbclient.util import run_sync
from nbformat.v4 import new_code_cell



class MimeType(str, Enum):
    """
    Represents a MIME type. 一个枚举类，定义了不同的 MIME 类型，用于表示 Jupyter 笔记本中不同类型的数据. 如纯文本、HTML、Markdown、图片、PDF、视频等。
    """

    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_MARKDOWN = "text/markdown"
    IMAGE_SVG = "image/svg+xml"
    IMAGE_PNG = "image/png"
    IMAGE_JPEG = "image/jpeg"
    VIDEO_MP4_B64 = "video/mp4/base64"
    APPLICATION_PDF = "application/pdf"
    TEXT_LATEX = "text/latex"
    APPLICATION_JSON = "application/json"
    APPLICATION_JAVASCRIPT = "application/javascript"


class Result:
    """
    一个类，用于表示执行 Jupyter 笔记本单元格后得到的结果。它可以包含多种类型的数据. 例如文本、HTML、Markdown、图片等。
    Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.
    The result is similar to the structure returned by ipython kernel: https://ipython.readthedocs.io/en/stable/development/execution.html#execution-semantics

    The result can contain multiple types of data, such as text, images, plots, etc. Each type of data is represented
    as a string, and the result can contain multiple types of data. The display calls don't have to have text representation,
    for the actual result the representation is always present for the result, the other representations are always optional.

    The class also provides methods to display the data in a Jupyter notebook.
    """

    text: Optional[str] = None
    html: Optional[str] = None
    markdown: Optional[str] = None
    svg: Optional[str] = None
    png: Optional[str] = None
    jpeg: Optional[str] = None
    pdf: Optional[str] = None
    mp4: Optional[str] = None
    latex: Optional[str] = None
    json: Optional[Dict[str, Any]] = None
    javascript: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    "Extra data that can be included. Not part of the standard types."

    is_main_result: bool
    "Whether this data is the result of the cell. Data can be produced by display calls of which can be multiple in a cell."

    raw: Dict[str, str]
    "Dictionary that maps MIME types to their corresponding string representations of the data."

    def __init__(self, is_main_result: bool, data: Dict[str, Any]):
        self.is_main_result = is_main_result
        self.raw = copy.deepcopy(data)

        self.text = data.pop(MimeType.TEXT_PLAIN, None)
        self.html = data.pop(MimeType.TEXT_HTML, None)
        self.markdown = data.pop(MimeType.TEXT_MARKDOWN, None)
        self.svg = data.pop(MimeType.IMAGE_SVG, None)
        self.png = data.pop(MimeType.IMAGE_PNG, None)
        self.jpeg = data.pop(MimeType.IMAGE_JPEG, None)
        self.pdf = data.pop(MimeType.APPLICATION_PDF, None)
        self.mp4 = data.pop(MimeType.VIDEO_MP4_B64, None)
        self.latex = data.pop(MimeType.TEXT_LATEX, None)
        self.json = data.pop(MimeType.APPLICATION_JSON, None)
        self.javascript = data.pop(MimeType.APPLICATION_JAVASCRIPT, None)
        self.extra = data
        # Only keeping the PNG representation if both PNG and JPEG are present
        if self.png and self.jpeg:
            del self.jpeg

    # Allows to iterate over formats()
    def __getitem__(self, key: Any) -> Any:
        return self.raw[key] if key in self.raw else getattr(self, key)

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return str(self.raw)

    def _repr_html_(self) -> Optional[str]:
        """
        Returns the HTML representation of the data.
        """
        return self.html

    def _repr_markdown_(self) -> Optional[str]:
        """
        Returns the Markdown representation of the data.
        """
        return self.markdown

    def _repr_svg_(self) -> Optional[str]:
        """
        Returns the SVG representation of the data.
        """
        return self.svg

    def _repr_png_(self) -> Optional[str]:
        """
        Returns the base64 representation of the PNG data.
        """
        return self.png

    def _repr_jpeg_(self) -> Optional[str]:
        """
        Returns the base64 representation of the JPEG data.
        """
        return self.jpeg

    def _repr_pdf_(self) -> Optional[str]:
        """
        Returns the PDF representation of the data.
        """
        return self.pdf

    def _repr_latex_(self) -> Optional[str]:
        """
        Returns the LaTeX representation of the data.
        """
        return self.latex

    def _repr_json_(self) -> Optional[dict]:
        """
        Returns the JSON representation of the data.
        """
        return self.json

    def _repr_javascript_(self) -> Optional[str]:
        """
        Returns the JavaScript representation of the data.
        """
        return self.javascript

    def formats(self) -> Iterable[str]:
        """
        Returns all available formats of the result.

        :return: All available formats of the result in MIME types.
        """
        formats = []
        if self.html:
            formats.append("html")
        if self.markdown:
            formats.append("markdown")
        if self.svg:
            formats.append("svg")
        if self.png:
            formats.append("png")
        if self.jpeg:
            formats.append("jpeg")
        if self.pdf:
            formats.append("pdf")
        if self.latex:
            formats.append("latex")
        if self.json:
            formats.append("json")
        if self.javascript:
            formats.append("javascript")
        if self.mp4:
            formats.append("mp4")
        if self.extra:
            formats.extend(iter(self.extra))
        return formats

def _remove_escape_and_color_codes(input_str: str) -> str:
    pattern = re.compile(r"\x1b\[[0-9;]*[mK]")
    return pattern.sub("", input_str)


class Logs(BaseModel):
    """
    用于存储在执行过程中打印到标准输出(stdout)和标准错误(stderr)的数据，通常由打印语句、日志、警告、子进程等生成。
    Data printed to stdout and stderr during execution, usually by print statements, logs, warnings, subprocesses, etc.
    """

    stdout: List[str] = []
    "List of strings printed to stdout by prints, subprocesses, etc."
    stderr: List[str] = []
    "List of strings printed to stderr by prints, subprocesses, etc."

    def __str__(self) -> str:
        stdout_str = "\n".join(self.stdout)
        stderr_str = "\n".join(self.stderr)
        return _remove_escape_and_color_codes(
            f"----- stdout -----\n{stdout_str}\n----- stderr -----\n{stderr_str}"
        )


class Error(BaseModel):
    """
    表示在执行单元格时发生的错误。它包含错误名称、错误值和追踪栈信息
    Represents an error that occurred during the execution of a cell.
    The error contains the name of the error, the value of the error, and the traceback.
    """

    name: str
    "Name of the exception."
    value: str
    "Value of the exception."
    traceback_raw: List[str]
    "List of strings representing the traceback."

    @property
    def traceback(self, return_clean_text: bool = True) -> str:
        """
        Returns the traceback as a single string.
        """
        text = "\n".join(self.traceback_raw)
        return _remove_escape_and_color_codes(text) if return_clean_text else text
    

class Execution(BaseModel):
    """
    用于表示单元格执行的结果。它可以包含结果列表、日志和错误对象。这个类提供了将执行结果转换为文本和 JSON 格式的方法。
    Represents the result of a cell execution.
    """

    class Config:
        arbitrary_types_allowed = True

    results: List[Result] = []
    "List of the result of the cell (interactively interpreted last line), display calls (e.g. matplotlib plots)."
    logs: Logs = Logs()
    "Logs printed to stdout and stderr during execution."
    error: Optional[Error] = None
    "Error object if an error occurred, None otherwise."

    def text(self, include_logs: bool = True) -> str:
        """
        Returns the text representation of this object, i.e. including the main result or the error traceback, optionally along with the logs (stdout, stderr).
        """
        prefix = str(self.logs) if include_logs else ""
        if self.error:
            return prefix + "\n----- Error -----\n" + self.error.traceback

        result_str = [
            (
                f"----- Final output -----\n{res.text}"
                if res.is_main_result
                else f"----- Intermediate output-----\n{res.text}"
            )
            for res in self.results
        ]
        return prefix + "\n" + "\n".join(result_str)

    @property
    def success(self) -> bool:
        """
        Returns whether the execution was successful.
        """
        return self.error is None

    def to_json(self) -> str:
        """
        Returns the JSON representation of the Execution object.
        """
        return self.model_dump_json(exclude_none=True)

    @field_serializer("results", when_used="json")
    def serialize_results(results: List[Result]) -> List[Dict[str, Union[str, bool]]]:  # type: ignore
        """
        Serializes the results to JSON.
        This method is used by the Pydantic JSON encoder.
        """
        serialized = []
        for result in results:
            serialized_dict = {key: result[key] for key in result.formats()}

            serialized_dict["text"] = result.text
            serialized_dict["is_main_result"] = result.is_main_result
            serialized.append(serialized_dict)
        return serialized

    @staticmethod
    def from_exception(exec: Exception, traceback_raw: List[str]) -> "Execution":
        """
        Creates an Execution object from an exception.
        """
        return Execution(
            error=Error(
                name=exec.__class__.__name__,
                value=str(exec),
                traceback_raw=traceback_raw,
            )
        )
    

class CodeInterpreter(abc.ABC):
    """Code interpreter interface."""

    def __init__(self, timeout: int, *args: Any, **kwargs: Any) -> None:
        self.timeout = timeout

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def close(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()

    def restart_kernel(self) -> None:
        raise NotImplementedError()

    def exec_cell(self, code: str) -> Execution:
        raise NotImplementedError()

    def exec_isolation(self, code: str) -> Execution:
        self.restart_kernel()
        return self.exec_cell(code)

    def upload_file(self, file: Union[str, Path, IO]) -> str:
        # Default behavior is a no-op (for local code interpreter)
        assert not isinstance(
            file, IO
        ), "Don't pass IO objects to upload_file() of local interpreter"
        return str(file)

    def download_file(self, file_path: str) -> Path:
        # Default behavior is a no-op (for local code interpreter)
        return Path(file_path)
    


class LocalCodeInterpreter(CodeInterpreter):
    """
    提供了一个本地代码解释器的功能，用于执行 Jupyter 笔记本单元格。它使用 nbclient 库来管理内核和执行单元格。
    """
    def __init__(self, timeout: int = 600) -> None:
        super().__init__(timeout=timeout)
        self.nb = nbformat.v4.new_notebook()
        self.nb_client = NotebookClient(self.nb, timeout=self.timeout)

    def _new_kernel(self) -> None:
        if self.nb_client.kc is None or not run_sync(self.nb_client.kc.is_alive)():  # type: ignore
            self.nb_client.create_kernel_manager()
            self.nb_client.start_new_kernel()
            self.nb_client.start_new_kernel_client()

    def close(self) -> None:
        if self.nb_client.km is not None and run_sync(self.nb_client.km.is_alive)():  # type: ignore
            run_sync(self.nb_client.km.shutdown_kernel)(now=True)
            run_sync(self.nb_client.km.cleanup_resources)()

            channels = [
                self.nb_client.kc.stdin_channel,
                self.nb_client.kc.hb_channel,
                self.nb_client.kc.control_channel,
            ]

            for ch in channels:
                if ch.is_alive():
                    ch.stop()

            self.nb_client.kc = None
            self.nb_client.km = None

    def restart_kernel(self) -> None:
        self.close()
        self.nb = nbformat.v4.new_notebook()
        self.nb_client = NotebookClient(self.nb, timeout=self.timeout)
        time.sleep(1)
        self._new_kernel()

    def exec_cell(self, code: str) -> Execution:
        try:
            self.nb.cells.append(new_code_cell(code))
            cell = self.nb.cells[-1]
            self.nb_client.execute_cell(cell, len(self.nb.cells) - 1)
            return _parse_local_code_interpreter_outputs(self.nb.cells[-1].outputs)
        except CellTimeoutError as e:
            run_sync(self.nb_client.km.interrupt_kernel)()  # type: ignore
            time.sleep(1)
            traceback_raw = traceback.format_exc().splitlines()
            return Execution.from_exception(e, traceback_raw)
        except DeadKernelError as e:
            self.restart_kernel()
            traceback_raw = traceback.format_exc().splitlines()
            return Execution.from_exception(e, traceback_raw)
        except Exception as e:
            traceback_raw = traceback.format_exc().splitlines()
            return Execution.from_exception(e, traceback_raw)
        
        
def _parse_local_code_interpreter_outputs(outputs: List[Dict[str, Any]]) -> Execution:
    """
    Parse notebook cell outputs to Execution object.
    Output types: https://nbformat.readthedocs.io/en/latest/format_description.html#code-cell-outputs
    """
    execution = Execution()
    for data in outputs:
        if data["output_type"] == "error":
            execution.error = Error(
                name=data["ename"],
                value=data["evalue"],
                traceback_raw=data["traceback"],
            )
        elif data["output_type"] == "stream":
            if data["name"] == "stdout":
                execution.logs.stdout.append(data["text"])
            elif data["name"] == "stderr":
                execution.logs.stderr.append(data["text"])
        elif data["output_type"] in "display_data":
            result = Result(is_main_result=False, data=data["data"])
            execution.results.append(result)
        elif data["output_type"] == "execute_result":
            result = Result(is_main_result=True, data=data["data"])
            execution.results.append(result)
        else:
            raise ValueError(f"Unknown output type: {data['output_type']}")
    return execution


def _remove_escape_and_color_codes(input_str: str) -> str:
    pattern = re.compile(r"\x1b\[[0-9;]*[mK]")
    return pattern.sub("", input_str)
