from documind.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_short_text_single_chunk():
    text = "One short sentence. Another short sentence."
    chunks = chunk_text(text, chunk_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert "One short sentence." in chunks[0].text
    assert "Another short sentence." in chunks[0].text


def test_default_params_produce_multiple_chunks_on_long_input():
    text = " ".join(f"Sentence number {i} about interviews and salaries." for i in range(1, 200))
    chunks = chunk_text(text)
    assert len(chunks) > 1


def test_word_count_boundary():
    text = " ".join(f"Sentence number {i} about interviews and salaries." for i in range(1, 60))
    chunks = chunk_text(text, chunk_size=40, overlap=8)
    assert len(chunks) > 1
    assert len(chunks[0].text.split()) <= 44


def test_overlap_carries_forward():
    text = " ".join(f"Sentence number {i} about interviews and salaries." for i in range(1, 60))
    chunks = chunk_text(text, chunk_size=40, overlap=8)
    tail = chunks[0].text.split()[-8:]
    head = chunks[1].text.split()[:8]
    assert tail == head


def test_zero_overlap_no_duplication():
    text = " ".join(f"Sentence number {i} about interviews and salaries." for i in range(1, 60))
    chunks = chunk_text(text, chunk_size=40, overlap=0)
    assert len(chunks) > 1
    tail = chunks[0].text.split()[-3:]
    head = chunks[1].text.split()[:3]
    assert tail != head


def test_indices_are_sequential():
    text = " ".join(f"Sentence number {i} about interviews and salaries." for i in range(1, 60))
    chunks = chunk_text(text, chunk_size=40, overlap=8)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_single_oversized_sentence_not_split():
    sentence = "Word " * 100 + "."
    chunks = chunk_text(sentence.strip(), chunk_size=10, overlap=2)
    assert len(chunks) == 1
    assert len(chunks[0].text.split()) == 101


def test_sentence_boundary_respected():
    text = "First sentence is short. Second sentence is also fairly short here."
    chunks = chunk_text(text, chunk_size=6, overlap=0)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.text.rstrip()[-1] in ".!?"
