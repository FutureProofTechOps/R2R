import string
from io import BytesIO
from typing import AsyncGenerator

from r2r.base.abstractions.document import DataType
from r2r.base.parsers.base_parser import AsyncParser

class PDFParser(AsyncParser[DataType]):
    """A parser for PDF data."""

    def __init__(self):
        try:
            from pypdf import PdfReader

            self.PdfReader = PdfReader
        except ImportError:
            raise ValueError(
                "Error, `pypdf` is required to run `PyPDFParser`. Please install it using `pip install pypdf`."
            )

    async def ingest(self, data: DataType) -> AsyncGenerator[str, None]:
        """Ingest PDF data and yield text from each page."""
        if isinstance(data, str):
            raise ValueError("PDF data must be in bytes format.")

        pdf = self.PdfReader(BytesIO(data))
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text is not None:
                page_text = "".join(
                    filter(lambda x: x in string.printable, page_text)
                )
                yield page_text


class PDFParserSix(AsyncParser[DataType]):
    """A parser for PDF data."""

    def __init__(self):
        try:
            from pdfminer.high_level import extract_text_to_fp
            from pdfminer.layout import LAParams
            self.extract_text_to_fp = extract_text_to_fp
            self.LAParams = LAParams
        except ImportError:
            raise ValueError(
                "Error, `pdfminer.six` is required to run `PDFParser`. Please install it using `pip install pdfminer.six`."
            )

    async def ingest(self, data: bytes) -> AsyncGenerator[str, None]:
        """Ingest PDF data and yield text from each page."""
        if not isinstance(data, bytes):
            raise ValueError("PDF data must be in bytes format.")

        pdf_file = BytesIO(data)
        
        async def process_page(page_number):
            output = BytesIO()
            await asyncio.to_thread(
                self.extract_text_to_fp,
                pdf_file,
                output,
                page_numbers=[page_number],
                laparams=self.LAParams(),
            )
            page_text = output.getvalue().decode('utf-8')
            return "".join(filter(lambda x: x in string.printable, page_text))

        from pdfminer.pdfparser import PDFParser as pdfminer_PDFParser
        from pdfminer.pdfdocument import PDFDocument

        parser = pdfminer_PDFParser(pdf_file)
        document = PDFDocument(parser)
        
        for page_number in range(len(list(document.get_pages()))):
            page_text = await process_page(page_number)
            if page_text:
                yield page_text

class PDFParserUnstructured(AsyncParser[DataType]):
    def __init__(self):
        # pdf parser
        try: 
            from unstructured.partition.pdf import partition_pdf
            self.partition_pdf = partition_pdf

        except ImportError:
            raise ValueError("Error, `pdfplumber` is required to run `PDFParserUnstructured`. Please install it using `pip install pdfplumber")
        
    async def ingest(self, data: DataType, partition_strategy: str = "hi_res") -> AsyncGenerator[str, None]:
        if isinstance(data, str):
            raise ValueError("PDF data must be in bytes format.")
        
        # partition the pdf
        elements = self.partition_pdf(data, partition_strategy = partition_strategy)
        for element in elements:
            yield element.text


class PDFParserMarker(AsyncParser[DataType]):
    def __init__(self):
        try:
            from marker.convert import convert_single_pdf
            from marker.models import load_all_models

            self.convert_single_pdf = convert_single_pdf
            if not self.model_refs: 
                self.model_refs = load_all_models()

        except ImportError as e:
            raise ValueError(f"Error, {e}")
                             
    def ingest(self, data: DataType) -> AsyncGenerator[str, None]:
        if isinstance(data, str):
            raise ValueError("PDF data must be in bytes format.")
        
        text, _, _ = self.convert_single_pdf(BytesIO(data), self.model_refs)
        yield text

class PDFParserLocal(AsyncParser[DataType]):
    def __init__(self):
        try:
            from r2r.parsers.common.layout_extraction import LayoutExtraction
            self.layout_parser = LayoutExtraction()
        except ImportError as e:
            raise ValueError(f"Error, {e}")
        
    
    async def ingest(self, data: DataType) -> AsyncGenerator[str, None]:
        if isinstance(data, str):
            raise ValueError("PDF data must be in bytes format.")
        
        layout = await self.layout_parser.ingest(data)


class PDFParserVLM(AsyncParser[DataType]):
    # todo
    def __init__(self):
        try:
            from r2r.parsers.common.layout_extraction import LayoutExtraction
            self.layout_parser = None
        except ImportError as e:
            raise ValueError(f"Error, {e}")
        
    
    async def ingest(self, data: DataType) -> AsyncGenerator[str, None]:
        if isinstance(data, str):
            raise ValueError("PDF data must be in bytes format.")
        
        layout = await self.layout_parser.ingest(data)
        yield layout

