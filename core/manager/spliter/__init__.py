"""
Document spliter module.

## 1. Document Spliter
used to convert documents to sort of markdown files, 
  which is standard ducument.

## 2. Usage
### 2.1 Example usage( for ms docx ):
```python
path = "/data/home/solgeo/temp/dv019_it_operation_guide_capdam_v2_5.docx"
encoder_path = "/data/home/solgeo/models/tiktoken_cache/cl100k_base.tiktoken"
output_path = "./temp/"

wtm = WordToMarkdown(
    docx_object=path,
    max_tokens=5000,
    encoder_path=encoder_path
)
wtm.parse(export_path=output_path)
```

### 2.2 Example usage( for pdf ):
```python
...
```

"""

from .word import WordSpliter

__all__ = [
    "WordSpliter",
]
