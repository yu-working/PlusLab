from setuptools import setup
import platform

# read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

install_requires = [
    "pypdf",
    "langchain>=0.1.0,<=0.1.16",
    "langchain_openai>=0.1.0",
    "chromadb==0.4.14",
    "openai>=0.27",
    "tiktoken",
    "scikit-learn<1.3.0",
    "jieba>=0.42.1",
    "sentence-transformers==2.2.2",
    "torch==2.0.1",
    "transformers>=4.41.1",  #==4.31.0
    "auto-gptq==0.3.1",
    "tqdm==4.65.0",
    "docx2txt==0.8",
    "rouge==1.0.1",
    "rouge-chinese==1.0.3",
    "bert-score==0.3.13",
    "click",
    "tokenizers>=0.19.1",
    "streamlit>=1.33.0",
    "streamlit_option_menu>=0.3.6",
    "rank_bm25",
    "unstructured",
    "python-pptx",
    "wikipedia",
    "akasha-plus"
]
if platform.system() == "Windows":
    install_requires.append("opencc==1.1.1")
elif platform.system() == "Darwin":
    install_requires.append("opencc==0.2")
else:
    install_requires.append('opencc==1.1.6')

setup(
    name="pluslab",
    version="0.1",
    description="A model testing tool based on Akasha-plus.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="cai yu tsai",
    url="https://github.com/yu-working/PlusLab",
    author_email="tsaiyuforwork@gmail.com",
    install_requires=install_requires,
    extra_requires={'llama-cpp': [
        "llama-cpp-python==0.2.6",
    ]},
    packages=["pluslab"],
    entry_points={"console_scripts": ["pluslab=pluslab.pluslab:main"]},
    python_requires=">=3.8",
)
