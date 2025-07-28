import os


def load_documents(directory: str) -> list[str]:
    """
    Loads all text files from a directory.
    """
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename)) as f:
                documents.append(f.read())
    return documents
