This service is used to detect if an image has clear signature and if the image contains anything other than the signature
The service uses Agent from pydantic_ai library.
There is some common code between this and agent_ocr. Since strictly speaking this is not OCR, the code / service is not merged with that of agent_ocr
Hence the code (base_node.py) has been replicated here